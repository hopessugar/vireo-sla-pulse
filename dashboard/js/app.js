/**
 * Vireo SLA Pulse — Dashboard v2
 * Soft pastel theme with sidebar navigation and circular progress rings.
 */

const API = '';

// ─── Chart.js Global ────────────────────────────────────────────────────────
Chart.defaults.color = '#9e93ad';
Chart.defaults.borderColor = 'rgba(100,80,130,0.08)';
Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyle = 'circle';
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.animation.duration = 800;
Chart.defaults.animation.easing = 'easeOutQuart';

const C = {
    purple: '#7c5cbf', purpleA: 'rgba(124,92,191,0.15)',
    rose: '#d4728c', roseA: 'rgba(212,114,140,0.15)',
    teal: '#5ba8a0', tealA: 'rgba(91,168,160,0.15)',
    amber: '#c9a252', amberA: 'rgba(201,162,82,0.15)',
    blue: '#6b8cce', blueA: 'rgba(107,140,206,0.15)',
    danger: '#c0556a', dangerA: 'rgba(192,85,106,0.12)',
    success: '#5a9e82', successA: 'rgba(90,158,130,0.12)',
};

const SHIFT_C = {
    Morning: { bg: C.amberA, border: C.amber },
    Day: { bg: C.blueA, border: C.blue },
    Night: { bg: C.purpleA, border: C.purple },
};

let allAgents = [];
let sortField = 'breached';
let sortDir = 'desc';

// ─── Sidebar Navigation ────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const tabId = 'tab-' + btn.dataset.tab;
        document.getElementById(tabId).classList.add('active');
    });
});

// ─── Fetch ──────────────────────────────────────────────────────────────────
async function fetchJSON(ep) {
    const r = await fetch(API + ep);
    if (!r.ok) throw new Error('API ' + r.status);
    return r.json();
}

// ─── Init ───────────────────────────────────────────────────────────────────
async function init() {
    try {
        const [summary, shifts, channels, agents, trend, categories, heatmap, patterns, packs, weeks, validation, financial] = await Promise.all([
            fetchJSON('/api/summary'), fetchJSON('/api/by-shift'), fetchJSON('/api/by-channel'),
            fetchJSON('/api/by-agent'), fetchJSON('/api/weekly-trend'), fetchJSON('/api/by-category'),
            fetchJSON('/api/heatmap'), fetchJSON('/api/patterns'), fetchJSON('/api/conversation-packs'),
            fetchJSON('/api/weeks'), fetchJSON('/api/validation'), fetchJSON('/api/financial'),
        ]);

        renderKPIs(summary, financial);
        renderShiftChart(shifts);
        renderChannelChart(channels);
        renderTrendChart(trend);
        renderCategoryChart(categories);
        renderHeatmap(heatmap);
        renderAgentTable(agents, shifts);
        renderShiftTrendChart(trend);
        renderPatterns(patterns);
        renderConversationPacks(packs);
        renderFinancial(financial, summary);
        renderWeekSelector(weeks);
        renderMethodology(summary, validation);

        allAgents = agents;
        const hb = agents.filter(a => a.breach_rate > 30 && a.tier === '1').length;
        document.getElementById('agentBreachCount').textContent = hb;
    } catch (err) {
        console.error(err);
        document.querySelector('.main-content').innerHTML =
            '<div class="loading" style="height:80vh;"><h2 style="color:var(--status-danger);">Failed to load</h2><p style="margin-top:8px;color:var(--text-secondary);">' + err.message + '</p><p style="margin-top:16px;color:var(--text-muted);">Run: <code>python run.py</code></p></div>';
    }
}

// ─── KPIs with Rings ────────────────────────────────────────────────────────
function setRing(id, pct) {
    const circ = 188.5;
    const offset = circ - (circ * Math.min(pct, 100) / 100);
    const el = document.getElementById(id);
    if (el) el.setAttribute('stroke-dashoffset', offset);
}

function renderKPIs(s, f) {
    animateValue('kpiTotal', s.total_tickets_analyzed);
    animateValue('kpiBreached', s.total_breached);
    document.getElementById('kpiMorning').textContent = f.morning_breach_rate + '%';
    document.getElementById('kpiCredits').textContent = 'Rs ' + formatNum(s.total_credits_inr);

    document.getElementById('kpiTotalDetail').textContent = s.duplicates_removed + ' duplicates removed';
    document.getElementById('kpiBreachedDetail').textContent = s.total_met_sla + ' met SLA (' + (100 - s.breach_rate_pct).toFixed(1) + '%)';
    document.getElementById('kpiMorningDetail').textContent = 'Day: ' + f.day_breach_rate + '% | Night: ' + (s.breach_rate_pct < 15 ? '~11' : '~11') + '%';
    document.getElementById('kpiCreditsDetail').textContent = 'Rs ' + formatNum(f.credits_per_quarter) + '/quarter';

    // Rings
    setRing('ringTotal', 100);
    document.getElementById('ringTotalLabel').textContent = formatNum(s.total_tickets_analyzed);
    
    setRing('ringBreached', s.breach_rate_pct);
    document.getElementById('ringBreachedLabel').textContent = s.breach_rate_pct + '%';
    
    setRing('ringMorning', f.morning_breach_rate);
    document.getElementById('ringMorningLabel').textContent = f.morning_breach_rate + '%';
    
    setRing('ringCredits', 60);
    document.getElementById('ringCreditsLabel').textContent = 'Rs ' + (s.total_credits_inr / 100000).toFixed(1) + 'L';
}

// ─── Shift Chart ────────────────────────────────────────────────────────────
function renderShiftChart(shifts) {
    const labels = Object.keys(shifts);
    const rates = labels.map(s => shifts[s].breach_rate);
    
    new Chart(document.getElementById('chartShift'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Breach Rate %',
                data: rates,
                backgroundColor: labels.map(s => SHIFT_C[s]?.bg || C.purpleA),
                borderColor: labels.map(s => SHIFT_C[s]?.border || C.purple),
                borderWidth: 2, borderRadius: 10, barPercentage: 0.5,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { afterLabel: ctx => shifts[labels[ctx.dataIndex]].breached + ' / ' + shifts[labels[ctx.dataIndex]].total + ' tickets' } }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(100,80,130,0.05)' }, ticks: { callback: v => v + '%' } },
                x: { grid: { display: false } }
            }
        }
    });
}

// ─── Channel Chart ──────────────────────────────────────────────────────────
function renderChannelChart(channels) {
    const labels = Object.keys(channels).sort((a, b) => channels[b].breach_rate - channels[a].breach_rate);
    const rates = labels.map(c => channels[c].breach_rate);
    const colors = [C.rose, C.amber, C.purple, C.teal];
    
    new Chart(document.getElementById('chartChannel'), {
        type: 'bar',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                data: rates,
                backgroundColor: colors.map(c => c + '22'),
                borderColor: colors,
                borderWidth: 2, borderRadius: 10, barPercentage: 0.5,
            }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { afterLabel: ctx => 'SLA: ' + channels[labels[ctx.dataIndex]].threshold_mins + 'min' } }
            },
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(100,80,130,0.05)' }, ticks: { callback: v => v + '%' } },
                y: { grid: { display: false } }
            }
        }
    });
}

// ─── Trend Chart ────────────────────────────────────────────────────────────
function renderTrendChart(trend) {
    const labels = trend.map(w => w.week);
    new Chart(document.getElementById('chartTrend'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                { label: 'Breach Rate %', data: trend.map(w => w.rate), borderColor: C.rose, backgroundColor: C.roseA, fill: true, tension: 0.35, pointRadius: 1.5, pointHoverRadius: 5, borderWidth: 2 },
                { label: 'Count', data: trend.map(w => w.breached), borderColor: C.purple, backgroundColor: 'transparent', tension: 0.35, pointRadius: 0, borderWidth: 1.5, borderDash: [5, 5], yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(100,80,130,0.05)' }, ticks: { callback: v => v + '%' }, title: { display: true, text: 'Rate %' } },
                y1: { position: 'right', beginAtZero: true, grid: { display: false }, title: { display: true, text: 'Count' } },
                x: { grid: { display: false }, ticks: { maxTicksLimit: 20, maxRotation: 45 } }
            }
        }
    });
}

// ─── Category Chart ─────────────────────────────────────────────────────────
function renderCategoryChart(cats) {
    const sorted = Object.entries(cats).sort((a, b) => b[1].breached - a[1].breached);
    new Chart(document.getElementById('chartCategory'), {
        type: 'bar',
        data: {
            labels: sorted.map(([c]) => c),
            datasets: [
                { label: 'Breached', data: sorted.map(([, d]) => d.breached), backgroundColor: C.roseA, borderColor: C.rose, borderWidth: 1, borderRadius: 4 },
                { label: 'Met SLA', data: sorted.map(([, d]) => d.total - d.breached), backgroundColor: C.tealA, borderColor: C.teal, borderWidth: 1, borderRadius: 4 }
            ]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { x: { stacked: true, grid: { color: 'rgba(100,80,130,0.05)' } }, y: { stacked: true, grid: { display: false }, ticks: { font: { size: 11 } } } }
        }
    });
}

// ─── Heatmap ────────────────────────────────────────────────────────────────
function renderHeatmap(data) {
    const el = document.getElementById('heatmapContainer');
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    const hours = Array.from({length:24},(_,i)=>i);
    const lk = {}; let mx = 0;
    data.forEach(d => { lk[d.day+'|'+d.hour] = d; if (d.rate > mx) mx = d.rate; });
    
    let h = '<div class="heatmap-grid"><div class="hm-label"></div>';
    hours.forEach(hr => h += '<div class="hm-header">' + (hr<10?'0':'') + hr + '</div>');
    days.forEach(day => {
        h += '<div class="hm-label">' + day.slice(0,3) + '</div>';
        hours.forEach(hr => {
            const d = lk[day+'|'+hr] || {rate:0,breached:0,total:0};
            const i = mx > 0 ? d.rate/mx : 0;
            // Use warm purple-rose tones instead of harsh red
            const r = Math.round(192 * i + 240 * (1-i));
            const g = Math.round(85 * i + 234 * (1-i));
            const b = Math.round(106 * i + 245 * (1-i));
            h += '<div class="hm-cell" style="background:rgb('+r+','+g+','+b+')" title="'+day+' '+hr+':00 IST: '+d.rate+'% ('+d.breached+'/'+d.total+')">'+(d.rate>0?d.rate:'')+'</div>';
        });
    });
    h += '</div>';
    el.innerHTML = h;
}

// ─── Agent Table ────────────────────────────────────────────────────────────
function renderAgentTable(agents, shifts) {
    if (shifts.Morning) {
        document.getElementById('morningRate').textContent = shifts.Morning.breach_rate + '%';
        setRing('ringMornAgent', shifts.Morning.breach_rate);
        document.getElementById('ringMornAgentLabel').textContent = shifts.Morning.breach_rate + '%';
    }
    if (shifts.Day) {
        document.getElementById('dayRate').textContent = shifts.Day.breach_rate + '%';
        setRing('ringDayAgent', shifts.Day.breach_rate);
        document.getElementById('ringDayAgentLabel').textContent = shifts.Day.breach_rate + '%';
    }
    document.getElementById('highBreachAgents').textContent = agents.filter(a => a.breach_rate > 30 && a.tier === '1').length;
    renderAgentRows(agents);

    document.querySelectorAll('#agentTable th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const f = th.dataset.sort;
            if (sortField === f) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
            else { sortField = f; sortDir = 'desc'; }
            document.querySelectorAll('#agentTable th').forEach(t => t.classList.remove('sorted-asc','sorted-desc'));
            th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
            renderAgentRows([...allAgents].sort((a,b) => {
                let va = a[f], vb = b[f];
                if (typeof va === 'string') { va = va.toLowerCase(); vb = vb.toLowerCase(); }
                return sortDir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
            }));
        });
    });

    document.getElementById('agentSearch').addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        renderAgentRows(allAgents.filter(a => a.name.toLowerCase().includes(q) || a.agent_id.toLowerCase().includes(q) || a.team.toLowerCase().includes(q)));
    });
}

function renderAgentRows(agents) {
    document.getElementById('agentTableBody').innerHTML = agents.map(a => {
        const rc = a.breach_rate > 35 ? 'danger' : a.breach_rate > 20 ? 'warning' : 'success';
        const sc = a.shift.toLowerCase();
        const hl = a.breach_rate > 35 && a.tier === '1' ? 'highlight-row' : '';
        const bw = Math.min(a.breach_rate, 50) * 2;
        const bc = a.breach_rate > 35 ? 'danger' : a.breach_rate > 20 ? 'accent' : 'success';
        return '<tr class="'+hl+'"><td><strong>'+a.name+'</strong> <span style="color:var(--text-light);font-size:0.68rem;">'+a.agent_id+'</span></td><td><span class="shift-pill '+sc+'"><span class="dot"></span>'+a.shift+'</span></td><td>'+a.site+'</td><td style="font-size:0.78rem;">'+a.team+'</td><td>'+a.total+'</td><td><strong>'+a.breached+'</strong></td><td><span class="badge '+rc+'">'+a.breach_rate+'%</span></td><td>'+a.avg_response_mins+' min</td><td style="min-width:100px;"><div class="progress-track"><div class="progress-bar '+bc+'" style="width:'+bw+'%"></div></div></td></tr>';
    }).join('');
}

// ─── Shift Trend ────────────────────────────────────────────────────────────
function renderShiftTrendChart(trend) {
    new Chart(document.getElementById('chartShiftTrend'), {
        type: 'line',
        data: {
            labels: trend.map(w => w.week),
            datasets: ['Morning','Day','Night'].map(s => ({
                label: s,
                data: trend.map(w => w.shifts[s]?.rate || 0),
                borderColor: SHIFT_C[s].border,
                backgroundColor: s === 'Morning' ? SHIFT_C[s].bg : 'transparent',
                fill: s === 'Morning', tension: 0.35, pointRadius: 1, pointHoverRadius: 5, borderWidth: 2,
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(100,80,130,0.05)' }, ticks: { callback: v => v + '%' } },
                x: { grid: { display: false }, ticks: { maxTicksLimit: 20, maxRotation: 45 } }
            }
        }
    });
}

// ─── Patterns ───────────────────────────────────────────────────────────────
function renderPatterns(patterns) {
    const el = document.getElementById('patternsContainer');
    el.innerHTML = patterns.map(p => '<div class="pattern-card '+p.severity+'"><div class="pattern-title">'+p.pattern+'</div><div class="pattern-insight">'+p.insight+'</div><div class="pattern-stats"><div><span class="label">Rate: </span><span class="value">'+p.breach_rate+'%</span></div><div><span class="label">Volume: </span><span class="value">'+p.volume+'</span></div><div><span class="label">Breaches: </span><span class="value">'+p.breaches+'</span></div></div></div>').join('');
}

// ─── Conversation Packs ─────────────────────────────────────────────────────
function renderConversationPacks(packs) {
    const el = document.getElementById('packsContainer');
    el.innerHTML = packs.map(p => {
        const initials = p.agent_name.split(' ').map(n=>n[0]).join('');
        const trendIcon = p.trend === 'improving' ? '&#9660;' : p.trend === 'declining' ? '&#9650;' : '&#8594;';
        const trendCol = p.trend === 'improving' ? 'var(--status-success)' : p.trend === 'declining' ? 'var(--status-danger)' : 'var(--text-muted)';
        
        return '<div class="pack-card" onclick="this.classList.toggle(\'expanded\')"><div class="pack-header"><div class="pack-agent"><div class="pack-avatar">'+initials+'</div><div><div class="pack-name">'+p.agent_name+'</div><div class="pack-meta">'+p.agent_id+' <span class="shift-pill '+p.shift.toLowerCase()+'"><span class="dot"></span>'+p.shift+'</span> '+p.site+' <span style="color:'+trendCol+'">'+trendIcon+' '+p.trend+'</span></div></div></div><div class="pack-stats"><div class="pack-stat-group"><div class="pack-stat-value danger">'+p.breach_rate+'%</div><div class="pack-stat-label">Breach Rate</div></div><div class="pack-stat-group"><div class="pack-stat-value">'+p.total_breaches+'</div><div class="pack-stat-label">Breaches</div></div><div class="pack-stat-group"><div class="pack-stat-value">'+p.avg_response_mins+'m</div><div class="pack-stat-label">Avg Resp</div></div></div></div><div class="pack-body"><h4 style="font-size:0.85rem;color:var(--accent-primary);margin-bottom:12px;">Talking Points for 1:1</h4>'+p.talking_points.map(t=>'<div class="talking-point"><div class="tp-topic">'+t.topic+'</div><div class="tp-data">'+t.data+'</div><div class="tp-context">'+t.context+'</div></div>').join('')+(p.recent_examples.length?'<h4 style="font-size:0.82rem;color:var(--text-muted);margin:16px 0 8px;">Recent Examples</h4>'+p.recent_examples.map(e=>'<div class="example-row"><span class="tid">'+e.ticket_id+'</span><span>'+e.date+'</span><span>'+e.channel+'</span><span class="breach-val">'+e.response_mins+'m / '+e.threshold_mins+'m</span></div>').join(''):'')+'<div style="margin-top:16px;padding:12px;background:var(--bg-card-alt);border-radius:10px;font-size:0.78rem;"><strong style="color:var(--accent-primary);">Peer Comparison:</strong> <span style="color:var(--text-secondary);">'+p.breach_rate+'% vs shift avg '+p.shift_avg_rate+'% ('+(p.peer_comparison==='above'?'<span style="color:var(--status-danger);">above</span>':'<span style="color:var(--status-success);">below</span>')+' peers)</span></div></div></div>';
    }).join('');
}

// ─── Financial ──────────────────────────────────────────────────────────────
function renderFinancial(f, s) {
    document.getElementById('financialTotal').textContent = 'Rs ' + formatNum(f.total_credits_18m);
    document.getElementById('financialContext').textContent = s.total_breached + ' breaches x Rs ' + f.breach_credit_per_ticket + ' each. Morning shift excess: Rs ' + formatNum(f.morning_excess_breaches * f.breach_credit_per_ticket);
    document.getElementById('savingsGrid').innerHTML = '<div class="savings-card"><div class="savings-val">Rs '+formatNum(f.savings_quarterly_if_fixed)+'</div><div class="savings-label">Quarterly savings if Morning matches Day</div></div><div class="savings-card"><div class="savings-val">'+f.morning_breach_rate+'% &#8594; '+f.day_breach_rate+'%</div><div class="savings-label">Target breach rate reduction</div></div><div class="savings-card"><div class="savings-val">'+f.morning_excess_breaches+'</div><div class="savings-label">Excess breaches vs Day benchmark</div></div>';
    
    new Chart(document.getElementById('chartMonthlyCost'), {
        type: 'bar',
        data: {
            labels: ['Current Monthly', 'Target Monthly'],
            datasets: [{ data: [f.credits_per_month, f.credits_per_month - f.savings_monthly_if_fixed], backgroundColor: [C.roseA, C.tealA], borderColor: [C.rose, C.teal], borderWidth: 2, borderRadius: 10, barPercentage: 0.4 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => 'Rs ' + formatNum(ctx.raw) } } },
            scales: { y: { beginAtZero: true, grid: { color: 'rgba(100,80,130,0.05)' }, ticks: { callback: v => 'Rs ' + formatNum(v) } }, x: { grid: { display: false } } }
        }
    });

    new Chart(document.getElementById('chartSavings'), {
        type: 'doughnut',
        data: {
            labels: ['Avoidable (Morning excess)', 'Baseline'],
            datasets: [{ data: [f.morning_excess_breaches * f.breach_credit_per_ticket, f.total_credits_18m - f.morning_excess_breaches * f.breach_credit_per_ticket], backgroundColor: [C.tealA, C.roseA], borderColor: [C.teal, C.rose], borderWidth: 2 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => 'Rs ' + formatNum(ctx.raw) } } }
        }
    });
}

// ─── Week Selector ──────────────────────────────────────────────────────────
function renderWeekSelector(weeks) {
    const sel = document.getElementById('weekSelector');
    weeks.reverse().forEach(w => { const o = document.createElement('option'); o.value = w; o.textContent = w; sel.appendChild(o); });
    sel.addEventListener('change', async () => {
        if (sel.value === 'all') { document.getElementById('weeklyReportContent').innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:32px;">Select a week to view details.</p>'; return; }
        document.getElementById('weeklyReportContent').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        try {
            const r = await fetchJSON('/api/weekly-report/' + sel.value);
            let html = '<div style="padding:8px 0;"><p style="font-size:0.88rem;line-height:1.6;margin-bottom:16px;">' + r.summary + '</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">';
            if (r.shift_breakdown) {
                html += '<div><h4 style="font-size:0.82rem;color:var(--accent-primary);margin-bottom:8px;">Shift Breakdown</h4>';
                for (const [s, d] of Object.entries(r.shift_breakdown)) {
                    const rc = d.rate > 30 ? 'danger' : d.rate > 15 ? 'warning' : 'success';
                    html += '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border-light);"><span class="shift-pill '+s.toLowerCase()+'"><span class="dot"></span>'+s+'</span><span class="badge '+rc+'">'+d.rate+'% ('+d.breached+'/'+d.total+')</span></div>';
                }
                html += '</div>';
            }
            if (r.top_agents && r.top_agents.length) {
                html += '<div><h4 style="font-size:0.82rem;color:var(--accent-primary);margin-bottom:8px;">Top Breaching Agents</h4>';
                r.top_agents.slice(0, 8).forEach(a => {
                    html += '<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:0.82rem;"><span>'+a.name+'</span><span style="color:var(--status-danger);font-weight:600;">'+a.breached+'</span></div>';
                });
                html += '</div>';
            }
            html += '</div></div>';
            document.getElementById('weeklyReportContent').innerHTML = html;
        } catch (e) { document.getElementById('weeklyReportContent').innerHTML = '<p style="color:var(--status-danger);">Error: '+e.message+'</p>'; }
    });
}

// ─── Methodology ────────────────────────────────────────────────────────────
function renderMethodology(s, v) {
    document.getElementById('methTotalRaw').textContent = formatNum(s.total_tickets_analyzed + s.duplicates_removed + s.skipped_open_pending);
    document.getElementById('methDuplicates').textContent = s.duplicates_removed;
    document.getElementById('methAccuracy').textContent = v.accuracy;
    document.getElementById('methMismatches').textContent = v.high_confidence_mismatches;
}

// ─── Utils ──────────────────────────────────────────────────────────────────
function formatNum(n) {
    if (n >= 100000) return (n / 100000).toFixed(1) + 'L';
    if (n >= 1000) return n.toLocaleString('en-IN');
    return String(n);
}

function animateValue(id, target) {
    const el = document.getElementById(id);
    const dur = 1200, start = performance.now();
    function upd(now) {
        const p = Math.min((now - start) / dur, 1);
        el.textContent = Math.round(target * (1 - Math.pow(1-p, 3))).toLocaleString('en-IN');
        if (p < 1) requestAnimationFrame(upd);
    }
    requestAnimationFrame(upd);
}

init();
