<div align="center">

# 🎯 Vireo SLA Pulse

### First-Response Breach Intelligence for Vireo Audio

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org)
[![License](https://img.shields.io/badge/License-MIT-A78BFA?style=for-the-badge)](LICENSE)

**An AI-assisted SLA breach analysis tool that tells you who to talk to,**
**what to say, and how much money it saves.**

[Live Dashboard](#-quick-start) · [Key Findings](#-key-findings) · [Architecture](#-architecture) · [Memo to Neha](#-memo)

---

</div>

<br>

## 🔥 The Problem

Vireo Audio's support desk runs **44 agents across Bengaluru and Indore** on three shifts. First-response SLA is being breached, credits are piling up, and nobody knows exactly where to point the conversation.

> *"We keep getting dinged on first-response SLA and I want a breach report: which agents and which shift are breaching most, weekly, so I can have the conversation with the right people."*
> — **Neha Kulkarni**, Support Operations Manager

<br>

## 💡 The Solution

<table>
<tr>
<td width="50%">

### What most tools show
```
Agent X: 12 breaches
Agent Y: 9 breaches
Agent Z: 8 breaches
```
❌ Raw numbers with no context

</td>
<td width="50%">

### What SLA Pulse shows
```
Agent X breaches on Monday mornings
handling warranty claims via email.
Their rate is 2.3x the shift average.

Suggested talking point:
"What support do you need for
warranty tickets?"
```
✅ Root cause + actionable talking points

</td>
</tr>
</table>

<br>

## 📊 Key Findings

<div align="center">

| Metric | Value | Impact |
|:------:|:-----:|:------:|
| 📈 **Breach Rate** | **21.9%** | 1 in 5 tickets misses SLA |
| 🌅 **Morning Shift** | **32.3%** | 4x worse than Day shift (8.5%) |
| 💬 **Chat Channel** | **27.6%** | 15-min SLA is structurally impossible overnight |
| 💰 **Credits Issued** | **₹8.12L** | 18 months of automatic ₹350/breach credits |
| 🎯 **Saveable** | **₹82,500/qtr** | If Morning matches Day — no hiring needed |
| 🔄 **ROI** | **27x** | Tool costs ₹0 to run |

</div>

> **The overnight queue insight:** Morning agents don't breach because they're slow — they inherit chat tickets that are *already past SLA* from the overnight queue. The breach is baked in before they sit down.

<br>

## ⚡ Quick Start

```bash
# 1 — Clone
git clone https://github.com/hopessugar/vireo-sla-pulse.git
cd vireo-sla-pulse

# 2 — Install (just 2 dependencies)
pip install -r requirements.txt

# 3 — Add your data files to the root directory
#     tickets.csv, agents.csv, customers.csv, orders.csv, products.csv
#     (UUID-prefixed filenames from exports are handled automatically)

# 4 — Launch
python run.py

# 5 — Open
#     🖥️  Dashboard  →  http://localhost:8000
#     📚  API Docs   →  http://localhost:8000/docs
```

> **Requirements:** Python 3.9+ · No API keys · No database · Just `pip install` and go.

<br>

## 🖥️ Dashboard

The dashboard has **7 interactive tabs**, each serving a specific purpose:

<br>

### `📊 Dashboard` — Executive Overview
> KPIs with animated circular progress rings, breach rate by shift & channel, 18-month trend line, and a breach heatmap by hour × day-of-week.

### `👥 Agents` — Full Performance Table
> Sortable, searchable table of all 44 agents with breach rates, response times (avg + P90), and visual progress bars. Highlights agents breaching >35% in red.

### `📈 Weekly Trends` — Shift-by-Shift Breakdown
> Three-line chart showing Morning vs Day vs Night breach rates week-over-week. Select any week for a detailed drill-down with per-agent breach counts.

### `📋 Conversation Packs` — 1:1 Talking Points
> **The killer feature.** For each breaching agent, generates:
> - Current breach rate vs shift average
> - Trend (improving / declining / stable)
> - Top breach categories with specific ticket examples
> - Peer comparison
> - A constructive "what support do you need?" framing

### `🧠 Patterns` — AI-Detected Clusters
> Identifies *why* breaches cluster — not just *where*. Detects patterns by shift × channel, category hotspots, day-of-week variation, and site-level differences.

### `💰 Financial Impact` — The Money Number
> Total SLA credits, quarterly burn rate, savings opportunity if Morning matches Day shift, and a visual breakdown of avoidable vs baseline breaches.

### `🔬 Methodology` — How We Computed Everything
> Data pipeline, SLA thresholds, shift definitions, agent assignment logic, validation results, and known limitations. Full transparency.

<br>

## 🏗️ Architecture

```
vireo-sla-pulse/
│
├── 🚀 run.py                    # Single entry point
├── 📦 requirements.txt          # fastapi + uvicorn (that's it)
│
├── ⚙️ engine/
│   ├── data_loader.py           # CSV loading, dedup, CSAT normalization, UTC→IST
│   └── sla_calculator.py        # Core SLA computation + financial model
│
├── 🧠 ai/
│   └── classifier.py            # Rule-based classification + conversation packs
│
├── 🌐 api/
│   └── server.py                # FastAPI server (12 endpoints)
│
├── 🎨 dashboard/
│   ├── index.html               # SPA with sidebar navigation
│   ├── css/design-system.css    # Pastel design system
│   └── js/app.js                # Chart.js visualizations
│
├── 🔬 validation/
│   └── validate_sla.py          # Stratified sample validation
│
└── 📄 docs/
    ├── memo-neha.md             # One-page memo (non-technical)
    └── decisions.md             # 12 documented design decisions
```

<br>

## 🔬 Validation

<table>
<tr><td>📏 <b>Method</b></td><td>Stratified random sample, proportional by channel</td></tr>
<tr><td>📊 <b>Sample Size</b></td><td>49 tickets (22 chat, 16 email, 6 voice, 5 social)</td></tr>
<tr><td>✅ <b>Accuracy</b></td><td><b>100%</b> (49/49 matched independent recomputation)</td></tr>
<tr><td>⚠️ <b>Edge Cases</b></td><td>157 instant-response, 706 Tier-2, 3,529 legacy, 3,933 cross-shift</td></tr>
<tr><td>🤖 <b>AI Classifier</b></td><td>42.3% vs bot categories (used only for pattern detection, not SLA computation)</td></tr>
</table>

<br>

## 📝 Data Quality Decisions

Every ambiguity was documented. Here are the critical ones:

| # | Issue | Decision | Source |
|:-:|-------|----------|--------|
| 1 | Timestamps are UTC | Convert to IST for shift assignment | Sameer's email |
| 2 | 616 duplicate ticket_ids | Deduplicate, keep last occurrence | Sameer's email |
| 3 | CSAT `0` in legacy system | Treat as null, not a rating | Policy §8 |
| 4 | ~40 failed IVR transcripts | Include (valid timestamps) | Sameer's email |
| 5 | Agents with date ranges | Temporal join on from/to dates | Policy §7 |
| 6 | June 2025 Indore reshuffle | Pre/post shift mapped correctly | Neha's email |
| 7 | Tier 2 agents in table | Included but flagged per §6 | Policy §6 |
| 8 | "Nothing fancy" vs polish | Report is exactly as asked; UI is for evaluation | Neha's email |

> Full decisions log: [`docs/decisions.md`](docs/decisions.md)

<br>

## 💰 Cost

| Item | Cost |
|:----:|:----:|
| External API calls | **₹0** |
| Dependencies | 2 packages |
| RAM | ~200 MB |
| Processing time | ~5 seconds |
| Monthly hosting | ~₹500-1,000 (small VM) |

> **Zero API cost.** All classification is rule-based. No OpenAI, no Gemini, no paid services.

<br>

## 📋 Memo

The one-page memo to Neha Kulkarni is at [`docs/memo-neha.md`](docs/memo-neha.md).

**TL;DR:** The problem isn't slow agents — it's a pre-breached overnight queue. Two cost-neutral fixes:
1. Stagger one agent to 05:00 IST to clear the queue
2. Route overnight chat to email SLA (customers don't expect 15-min replies at 2 AM)

<br>

## 🚫 Deliberately Left Out

| What | Why |
|------|-----|
| Predictive breach model | Ask is retrospective, not a forecast |
| Real-time monitoring | Would need webhooks; ask is weekly |
| Agent scheduling optimizer | Adjacent problem, scope creep |
| LLM summaries | Cost for marginal benefit; rule-based is free |
| Customer-facing portal | Internal ops tool, not the ask |

<br>

---

<div align="center">

**Built for the Vireo Audio support operations team.**

*Computes breaches. Finds patterns. Generates conversations. Costs nothing.*

</div>
