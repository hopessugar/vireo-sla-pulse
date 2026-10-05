"""
Vireo SLA Pulse — SLA Calculator
Core SLA breach computation engine.
Handles UTC→IST conversion, per-channel thresholds, shift assignment, and weekly aggregation.

SLA Thresholds (from support-policy.pdf §3):
  - Chat:           15 minutes
  - Voice callback:  2 hours (120 minutes)
  - Social:          4 hours (240 minutes)
  - Email:           8 hours (480 minutes)

Breach credit: Rs 350 per breached ticket (§3)
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from engine.data_loader import parse_datetime, utc_to_ist, get_agent_info_at_date

# SLA thresholds in minutes (from support-policy.pdf §3)
SLA_THRESHOLDS = {
    'chat': 15,
    'voice': 120,
    'social': 240,
    'email': 480,
}

# Breach credit per ticket (from support-policy.pdf §3)
BREACH_CREDIT_INR = 350

# Cost standards (from support-policy.pdf §4)
COST_PER_CONTACT = {
    'chat': 210,
    'email': 260,
    'voice': 520,
    'social': 240,
}
BLENDED_COST_PER_CONTACT = 290
COST_PER_TRANSFER = 305
AGENT_COST_PER_HOUR = 165
AGENT_SHIFT_HOURS = 8

# Shift definitions IST (from support-policy.pdf §7)
# Morning: 06:00-14:00, Day: 14:00-22:00, Night: 22:00-06:00
SHIFT_DEFINITIONS = {
    'Morning': (6, 14),   # 06:00 IST to 14:00 IST
    'Day': (14, 22),      # 14:00 IST to 22:00 IST
    'Night': (22, 6),     # 22:00 IST to 06:00 IST (wraps midnight)
}


def get_shift_for_time(ist_hour: int) -> str:
    """Determine which shift owns a given IST hour."""
    if 6 <= ist_hour < 14:
        return 'Morning'
    elif 14 <= ist_hour < 22:
        return 'Day'
    else:
        return 'Night'


def compute_response_time(created_utc: datetime, responded_utc: datetime) -> float:
    """Compute first-response time in minutes."""
    delta = (responded_utc - created_utc).total_seconds() / 60
    return max(0, delta)  # Guard against negative (data issues)


def is_breach(response_time_mins: float, channel: str) -> bool:
    """Check if response time exceeds SLA threshold for the channel."""
    threshold = SLA_THRESHOLDS.get(channel, 480)
    return response_time_mins > threshold


def compute_all_breaches(tickets: List[Dict], agent_lookup: Dict) -> Dict:
    """
    Main SLA computation engine.
    For each ticket, computes:
      - Response time in minutes
      - Whether it breached SLA
      - Shift at time of creation (IST)
      - Agent info at time of ticket
      - Week key for aggregation
    
    Returns comprehensive breach data structure.
    """
    results = {
        'ticket_breaches': [],       # Per-ticket breach details
        'by_agent': defaultdict(lambda: {'breached': 0, 'total': 0, 'resp_times': [],
                                         'name': '', 'shift': '', 'site': '', 'team': '', 'tier': '1',
                                         'breach_categories': defaultdict(int),
                                         'breach_channels': defaultdict(int)}),
        'by_shift': defaultdict(lambda: {'breached': 0, 'total': 0, 'resp_times': []}),
        'by_channel': defaultdict(lambda: {'breached': 0, 'total': 0, 'resp_times': [],
                                           'threshold': 0}),
        'by_week': defaultdict(lambda: {'breached': 0, 'total': 0}),
        'by_agent_week': defaultdict(lambda: {'breached': 0, 'total': 0}),
        'by_shift_week': defaultdict(lambda: {'breached': 0, 'total': 0}),
        'by_category': defaultdict(lambda: {'breached': 0, 'total': 0}),
        'by_site': defaultdict(lambda: {'breached': 0, 'total': 0}),
        'by_hour_dow': defaultdict(lambda: {'breached': 0, 'total': 0}),
        'summary': {
            'total_valid': 0,
            'total_breached': 0,
            'total_met': 0,
            'total_credits_inr': 0,
            'skipped_open_pending': 0,
            'skipped_no_data': 0,
        },
    }
    
    for t in tickets:
        # Skip open/pending tickets — no resolution to judge
        if t.get('status') in ('open', 'pending'):
            results['summary']['skipped_open_pending'] += 1
            continue
        
        created_utc = parse_datetime(t.get('created_at', ''))
        responded_utc = parse_datetime(t.get('first_response_at', ''))
        
        if not created_utc or not responded_utc:
            results['summary']['skipped_no_data'] += 1
            continue
        
        # Compute response time
        resp_mins = compute_response_time(created_utc, responded_utc)
        channel = t.get('channel', 'email')
        breached = is_breach(resp_mins, channel)
        
        # Convert to IST for shift determination
        created_ist = utc_to_ist(created_utc)
        ticket_shift = get_shift_for_time(created_ist.hour)
        
        # Get agent info at ticket time (temporal join)
        agent_id = t.get('agent_id', '')
        agent_info = get_agent_info_at_date(agent_lookup, agent_id, created_utc)
        
        # Week key (ISO year-week based on IST date)
        week_key = created_ist.strftime('%Y-W%W')
        
        # Day of week and hour for heatmap
        dow = created_ist.strftime('%A')
        hour = created_ist.hour
        
        # Update summary
        results['summary']['total_valid'] += 1
        
        # Store per-ticket breach info
        ticket_detail = {
            'ticket_id': t['ticket_id'],
            'created_utc': created_utc.strftime('%Y-%m-%d %H:%M'),
            'created_ist': created_ist.strftime('%Y-%m-%d %H:%M'),
            'responded_utc': responded_utc.strftime('%Y-%m-%d %H:%M'),
            'response_mins': round(resp_mins, 1),
            'channel': channel,
            'threshold_mins': SLA_THRESHOLDS.get(channel, 480),
            'breached': breached,
            'agent_id': agent_id,
            'agent_name': agent_info['name'],
            'agent_shift': agent_info['shift'],  # Agent's rostered shift
            'ticket_shift': ticket_shift,          # Shift when ticket was created
            'site': agent_info['site'],
            'team': agent_info['team'],
            'tier': agent_info['tier'],
            'category': t.get('category', 'Unknown'),
            'priority': t.get('priority', 'Normal'),
            'source_system': t.get('source_system', 'helpdesk'),
            'week': week_key,
            'dow': dow,
            'hour': hour,
            'status': t.get('status', ''),
            'csat': t.get('csat_score_normalized'),
            'transfers': int(t.get('transfers', 0) or 0),
        }
        results['ticket_breaches'].append(ticket_detail)
        
        # Aggregate by agent
        ag = results['by_agent'][agent_id]
        ag['total'] += 1
        ag['resp_times'].append(resp_mins)
        ag['name'] = agent_info['name']
        ag['shift'] = agent_info['shift']
        ag['site'] = agent_info['site']
        ag['team'] = agent_info['team']
        ag['tier'] = agent_info['tier']
        
        # Aggregate by shift (agent's rostered shift)
        results['by_shift'][agent_info['shift']]['total'] += 1
        results['by_shift'][agent_info['shift']]['resp_times'].append(resp_mins)
        
        # Aggregate by channel
        ch_data = results['by_channel'][channel]
        ch_data['total'] += 1
        ch_data['resp_times'].append(resp_mins)
        ch_data['threshold'] = SLA_THRESHOLDS.get(channel, 480)
        
        # Aggregate by week
        results['by_week'][week_key]['total'] += 1
        
        # Aggregate by agent+week
        results['by_agent_week'][f"{agent_id}|{week_key}"]['total'] += 1
        
        # Aggregate by shift+week
        results['by_shift_week'][f"{agent_info['shift']}|{week_key}"]['total'] += 1
        
        # Aggregate by category
        results['by_category'][t.get('category', 'Unknown')]['total'] += 1
        
        # Aggregate by site
        results['by_site'][agent_info['site']]['total'] += 1
        
        # Aggregate by hour x dow (for heatmap)
        results['by_hour_dow'][f"{dow}|{hour}"]['total'] += 1
        
        if breached:
            results['summary']['total_breached'] += 1
            results['summary']['total_credits_inr'] += BREACH_CREDIT_INR
            
            ag['breached'] += 1
            ag['breach_categories'][t.get('category', 'Unknown')] += 1
            ag['breach_channels'][channel] += 1
            
            results['by_shift'][agent_info['shift']]['breached'] += 1
            ch_data['breached'] += 1
            results['by_week'][week_key]['breached'] += 1
            results['by_agent_week'][f"{agent_id}|{week_key}"]['breached'] += 1
            results['by_shift_week'][f"{agent_info['shift']}|{week_key}"]['breached'] += 1
            results['by_category'][t.get('category', 'Unknown')]['breached'] += 1
            results['by_site'][agent_info['site']]['breached'] += 1
            results['by_hour_dow'][f"{dow}|{hour}"]['breached'] += 1
    
    results['summary']['total_met'] = (
        results['summary']['total_valid'] - results['summary']['total_breached']
    )
    
    # Compute derived metrics
    _compute_agent_metrics(results)
    _compute_trend_analysis(results)
    
    return results


def _compute_agent_metrics(results: Dict):
    """Compute per-agent derived metrics: avg response time, breach rate, percentile."""
    agent_data = results['by_agent']
    
    # Compute metrics for each agent
    for aid, data in agent_data.items():
        if data['total'] > 0:
            data['breach_rate'] = round(data['breached'] / data['total'] * 100, 1)
            data['avg_resp_mins'] = round(sum(data['resp_times']) / len(data['resp_times']), 1)
            sorted_times = sorted(data['resp_times'])
            p50_idx = len(sorted_times) // 2
            p90_idx = int(len(sorted_times) * 0.9)
            data['p50_resp_mins'] = round(sorted_times[p50_idx], 1)
            data['p90_resp_mins'] = round(sorted_times[min(p90_idx, len(sorted_times)-1)], 1)
        else:
            data['breach_rate'] = 0
            data['avg_resp_mins'] = 0
            data['p50_resp_mins'] = 0
            data['p90_resp_mins'] = 0


def _compute_trend_analysis(results: Dict):
    """Compute weekly trend with moving averages and shift comparisons."""
    weeks = sorted(results['by_week'].keys())
    
    trend = []
    for w in weeks:
        d = results['by_week'][w]
        total = d['total']
        breached = d['breached']
        rate = round(breached / total * 100, 1) if total > 0 else 0
        
        # Per-shift breakdown for this week
        shift_breakdown = {}
        for shift_name in ['Morning', 'Day', 'Night']:
            sw_key = f"{shift_name}|{w}"
            sw_data = results['by_shift_week'].get(sw_key, {'breached': 0, 'total': 0})
            sw_total = sw_data['total']
            sw_breached = sw_data['breached']
            sw_rate = round(sw_breached / sw_total * 100, 1) if sw_total > 0 else 0
            shift_breakdown[shift_name] = {
                'total': sw_total,
                'breached': sw_breached,
                'rate': sw_rate,
            }
        
        trend.append({
            'week': w,
            'total': total,
            'breached': breached,
            'rate': rate,
            'shifts': shift_breakdown,
        })
    
    results['weekly_trend'] = trend


def compute_financial_impact(results: Dict, months: int = 18) -> Dict:
    """
    Compute financial impact of SLA breaches.
    Uses policy §3 (Rs 350 per breach credit) and §4 (cost standards).
    """
    total_breached = results['summary']['total_breached']
    total_credits = total_breached * BREACH_CREDIT_INR
    
    # Morning shift breach surplus
    morning_data = results['by_shift'].get('Morning', {'breached': 0, 'total': 0})
    day_data = results['by_shift'].get('Day', {'breached': 0, 'total': 0})
    
    morning_rate = morning_data['breached'] / morning_data['total'] if morning_data['total'] > 0 else 0
    day_rate = day_data['breached'] / day_data['total'] if day_data['total'] > 0 else 0
    
    # If morning matched day's rate, how many breaches saved?
    morning_excess = morning_data['breached'] - int(morning_data['total'] * day_rate)
    savings_if_morning_matches_day = morning_excess * BREACH_CREDIT_INR
    
    # Overall: if total breach rate dropped from current to day-shift level
    overall_excess = total_breached - int(results['summary']['total_valid'] * day_rate)
    overall_savings = overall_excess * BREACH_CREDIT_INR
    
    return {
        'total_credits_18m': total_credits,
        'credits_per_month': round(total_credits / months),
        'credits_per_quarter': round(total_credits / (months / 3)),
        'morning_breach_rate': round(morning_rate * 100, 1),
        'day_breach_rate': round(day_rate * 100, 1),
        'morning_excess_breaches': morning_excess,
        'savings_morning_to_day': savings_if_morning_matches_day,
        'savings_monthly_if_fixed': round(savings_if_morning_matches_day / months),
        'savings_quarterly_if_fixed': round(savings_if_morning_matches_day / (months / 3)),
        'overall_excess_breaches': overall_excess,
        'overall_savings': overall_savings,
        'breach_credit_per_ticket': BREACH_CREDIT_INR,
        'cost_standards': COST_PER_CONTACT,
        'blended_cost': BLENDED_COST_PER_CONTACT,
    }
