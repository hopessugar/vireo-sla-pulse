"""
Vireo SLA Pulse — AI Classifier & Conversation Pack Generator
Uses rule-based classification (zero API cost) with optional LLM enhancement.
Generates agent conversation packs — the 1:1 talking points Neha needs.
"""
from collections import defaultdict
from typing import List, Dict, Optional
import re
import json


# ─── Rule-based ticket classifier ───────────────────────────────────────────
# The intake bot already sets category. We validate/reclassify from customer_message text.

CATEGORY_KEYWORDS = {
    'Billing & Payments': [
        'refund', 'payment', 'charged', 'invoice', 'billing', 'money',
        'transaction', 'upi', 'credit', 'debit', 'cashback', 'coupon',
        'discount', 'price', 'overcharged', 'double charged', 'emi'
    ],
    'Delivery & Shipping': [
        'delivery', 'shipping', 'track', 'dispatch', 'courier', 'delayed',
        'not received', 'wrong address', 'lost package', 'out for delivery',
        'estimated delivery', 'shipped', 'transit'
    ],
    'Connectivity': [
        'bluetooth', 'pairing', 'disconnect', 'connection', 'wifi', 'sync',
        'not connecting', 'drops', 'interference', 'range', 'multipoint'
    ],
    'Audio Quality': [
        'sound', 'audio', 'bass', 'volume', 'noise cancel', 'distort',
        'crackling', 'one side', 'mono', 'muffled', 'echo', 'static',
        'left ear', 'right ear', 'anc'
    ],
    'Charging & Battery': [
        'battery', 'charging', 'charge', 'drain', 'not charging', 'case',
        'power', 'dead', 'usb-c', 'cable', 'low battery', 'battery life'
    ],
    'Returns & Refunds': [
        'return', 'replace', 'exchange', 'pickup', 'reverse', 'rma',
        'send back', 'damaged', 'defective', 'broken', 'doa'
    ],
    'Warranty & Repair': [
        'warranty', 'repair', 'claim', 'service center', 'fix', 'rma',
        'manufacturer defect', 'under warranty'
    ],
    'App & Firmware': [
        'app', 'firmware', 'update', 'software', 'crash', 'bug',
        'feature', 'equalizer', 'eq', 'settings', 'reset'
    ],
    'Account & Login': [
        'login', 'password', 'account', 'otp', 'register', 'sign up',
        'profile', 'email change', 'phone number'
    ],
    'Product Enquiry': [
        'color', 'size', 'compatible', 'feature', 'compare', 'which',
        'recommend', 'difference', 'vs', 'specification', 'spec'
    ],
}


def classify_ticket(customer_message: str) -> Dict:
    """
    Rule-based classification from customer message text.
    Returns dict with predicted category and confidence.
    """
    if not customer_message:
        return {'predicted_category': 'Other', 'confidence': 0, 'matched_keywords': []}
    
    msg_lower = customer_message.lower()
    scores = {}
    matched = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        cat_matches = [kw for kw in keywords if kw in msg_lower]
        scores[category] = len(cat_matches)
        matched[category] = cat_matches
    
    if not any(scores.values()):
        return {'predicted_category': 'Other', 'confidence': 0, 'matched_keywords': []}
    
    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]
    total_matches = sum(scores.values())
    confidence = round(max_score / max(total_matches, 1) * 100, 1)
    
    return {
        'predicted_category': best_cat,
        'confidence': confidence,
        'matched_keywords': matched[best_cat],
    }


def validate_categories(tickets: List[Dict]) -> Dict:
    """
    Compare bot-assigned categories vs our classification.
    Returns accuracy metrics.
    """
    total = 0
    correct = 0
    mismatches = []
    
    for t in tickets:
        bot_cat = t.get('category', '')
        msg = t.get('customer_message', '')
        if not msg or not bot_cat:
            continue
        
        result = classify_ticket(msg)
        predicted = result['predicted_category']
        total += 1
        
        if predicted == bot_cat:
            correct += 1
        elif result['confidence'] > 40:  # Only count high-confidence mismatches
            mismatches.append({
                'ticket_id': t.get('ticket_id'),
                'bot_category': bot_cat,
                'predicted': predicted,
                'confidence': result['confidence'],
            })
    
    return {
        'total_classified': total,
        'matching': correct,
        'accuracy': round(correct / max(total, 1) * 100, 1),
        'high_confidence_mismatches': len(mismatches),
        'sample_mismatches': mismatches[:20],
    }


# ─── Breach pattern detector ────────────────────────────────────────────────

def detect_breach_patterns(breach_results: Dict) -> List[Dict]:
    """
    Identify statistically significant breach patterns.
    Looks for clusters by: shift × channel, shift × category, agent × time-of-day.
    """
    patterns = []
    
    # Pattern 1: Morning shift + chat = worst combination
    morning_chat_breaches = 0
    morning_chat_total = 0
    for detail in breach_results['ticket_breaches']:
        if detail['agent_shift'] == 'Morning' and detail['channel'] == 'chat':
            morning_chat_total += 1
            if detail['breached']:
                morning_chat_breaches += 1
    
    if morning_chat_total > 0:
        rate = morning_chat_breaches / morning_chat_total * 100
        patterns.append({
            'pattern': 'Morning shift × Chat channel',
            'breach_rate': round(rate, 1),
            'volume': morning_chat_total,
            'breaches': morning_chat_breaches,
            'insight': f'Morning chat has a {rate:.0f}% breach rate — the overnight queue builds up and agents open to a backlog that exceeds the 15-min SLA by definition.',
            'severity': 'critical' if rate > 30 else 'warning',
        })
    
    # Pattern 2: Category-specific patterns
    for cat, data in breach_results['by_category'].items():
        if data['total'] > 50:
            rate = data['breached'] / data['total'] * 100
            overall_rate = breach_results['summary']['total_breached'] / breach_results['summary']['total_valid'] * 100
            if rate > overall_rate * 1.3:  # 30% above average
                patterns.append({
                    'pattern': f'High breach rate in {cat}',
                    'breach_rate': round(rate, 1),
                    'volume': data['total'],
                    'breaches': data['breached'],
                    'insight': f'{cat} tickets breach at {rate:.0f}% vs {overall_rate:.0f}% overall — may need specialized routing or templates.',
                    'severity': 'warning',
                })
    
    # Pattern 3: Site comparison
    for site, data in breach_results['by_site'].items():
        if data['total'] > 100:
            rate = data['breached'] / data['total'] * 100
            patterns.append({
                'pattern': f'{site} site performance',
                'breach_rate': round(rate, 1),
                'volume': data['total'],
                'breaches': data['breached'],
                'insight': f'{site} breach rate is {rate:.0f}%',
                'severity': 'info',
            })
    
    # Pattern 4: Day-of-week patterns
    dow_data = defaultdict(lambda: {'breached': 0, 'total': 0})
    for detail in breach_results['ticket_breaches']:
        dow = detail['dow']
        dow_data[dow]['total'] += 1
        if detail['breached']:
            dow_data[dow]['breached'] += 1
    
    worst_day = max(dow_data.items(), key=lambda x: x[1]['breached'] / max(x[1]['total'], 1))
    best_day = min(dow_data.items(), key=lambda x: x[1]['breached'] / max(x[1]['total'], 1))
    
    patterns.append({
        'pattern': 'Day-of-week variation',
        'breach_rate': round(worst_day[1]['breached'] / worst_day[1]['total'] * 100, 1),
        'volume': worst_day[1]['total'],
        'breaches': worst_day[1]['breached'],
        'insight': f'Worst day: {worst_day[0]} ({worst_day[1]["breached"]/worst_day[1]["total"]*100:.0f}%). Best: {best_day[0]} ({best_day[1]["breached"]/best_day[1]["total"]*100:.0f}%).',
        'severity': 'info',
    })
    
    return sorted(patterns, key=lambda p: p['breaches'], reverse=True)


# ─── Conversation Pack Generator ────────────────────────────────────────────

def generate_conversation_pack(agent_id: str, breach_results: Dict) -> Dict:
    """
    Generate a 1:1 conversation pack for a specific agent.
    This is what Neha needs — talking points backed by specific data.
    """
    agent_data = breach_results['by_agent'].get(agent_id)
    if not agent_data:
        return {'error': f'Agent {agent_id} not found'}
    
    # Get recent breach examples
    recent_breaches = [
        d for d in breach_results['ticket_breaches']
        if d['agent_id'] == agent_id and d['breached']
    ]
    recent_breaches.sort(key=lambda x: x['created_utc'], reverse=True)
    
    # Compute peer comparison (same shift agents)
    shift = agent_data['shift']
    peers = {
        aid: data for aid, data in breach_results['by_agent'].items()
        if data['shift'] == shift and data['tier'] == agent_data['tier']
    }
    peer_rates = [d['breach_rate'] for d in peers.values() if d['total'] > 20]
    shift_avg_rate = sum(peer_rates) / len(peer_rates) if peer_rates else 0
    
    # Compute trend (are they improving?)
    agent_weekly = {}
    for key, data in breach_results['by_agent_week'].items():
        parts = key.split('|')
        if parts[0] == agent_id:
            agent_weekly[parts[1]] = data
    
    weeks_sorted = sorted(agent_weekly.keys())
    if len(weeks_sorted) >= 8:
        first_half = weeks_sorted[:len(weeks_sorted)//2]
        second_half = weeks_sorted[len(weeks_sorted)//2:]
        
        first_breaches = sum(agent_weekly[w]['breached'] for w in first_half)
        first_total = sum(agent_weekly[w]['total'] for w in first_half)
        second_breaches = sum(agent_weekly[w]['breached'] for w in second_half)
        second_total = sum(agent_weekly[w]['total'] for w in second_half)
        
        first_rate = first_breaches / max(first_total, 1) * 100
        second_rate = second_breaches / max(second_total, 1) * 100
        
        if second_rate < first_rate * 0.85:
            trend = 'improving'
            trend_detail = f'Breach rate dropped from {first_rate:.0f}% to {second_rate:.0f}%'
        elif second_rate > first_rate * 1.15:
            trend = 'declining'
            trend_detail = f'Breach rate increased from {first_rate:.0f}% to {second_rate:.0f}%'
        else:
            trend = 'stable'
            trend_detail = f'Breach rate steady around {(first_rate+second_rate)/2:.0f}%'
    else:
        trend = 'insufficient_data'
        trend_detail = 'Not enough weekly data for trend analysis'
    
    # Top breach categories
    top_categories = sorted(
        agent_data['breach_categories'].items(),
        key=lambda x: x[1], reverse=True
    )[:3]
    
    # Generate talking points
    talking_points = []
    
    # Point 1: Current state
    talking_points.append({
        'topic': 'Current Performance',
        'data': f'{agent_data["breach_rate"]}% breach rate ({agent_data["breached"]} of {agent_data["total"]} tickets)',
        'context': f'Shift average is {shift_avg_rate:.1f}%. {"Above" if agent_data["breach_rate"] > shift_avg_rate else "Below"} peers by {abs(agent_data["breach_rate"] - shift_avg_rate):.1f}pp.',
    })
    
    # Point 2: Trend
    talking_points.append({
        'topic': 'Trend',
        'data': trend_detail,
        'context': 'Positive' if trend == 'improving' else 'Needs attention' if trend == 'declining' else 'Steady',
    })
    
    # Point 3: Problem categories
    if top_categories:
        cats_str = ', '.join(f'{cat} ({count})' for cat, count in top_categories)
        talking_points.append({
            'topic': 'Breach Concentration',
            'data': f'Most breaches in: {cats_str}',
            'context': 'Consider additional training or templates for these categories.',
        })
    
    # Point 4: Response time profile
    talking_points.append({
        'topic': 'Response Time',
        'data': f'Average: {agent_data["avg_resp_mins"]:.0f} min, P90: {agent_data["p90_resp_mins"]:.0f} min',
        'context': 'P90 shows worst-case performance — where the breaches cluster.',
    })
    
    # Point 5: Constructive question (per Priya's request — don't make it punitive)
    talking_points.append({
        'topic': 'Support Question',
        'data': 'What is making it hard to respond within SLA on these ticket types?',
        'context': 'Is it queue volume, ticket complexity, tooling, or something else?',
    })
    
    return {
        'agent_id': agent_id,
        'agent_name': agent_data['name'],
        'shift': shift,
        'site': agent_data['site'],
        'team': agent_data['team'],
        'breach_rate': agent_data['breach_rate'],
        'total_tickets': agent_data['total'],
        'total_breaches': agent_data['breached'],
        'avg_response_mins': agent_data['avg_resp_mins'],
        'p50_response_mins': agent_data['p50_resp_mins'],
        'p90_response_mins': agent_data['p90_resp_mins'],
        'trend': trend,
        'trend_detail': trend_detail,
        'shift_avg_rate': round(shift_avg_rate, 1),
        'peer_comparison': 'above' if agent_data['breach_rate'] > shift_avg_rate else 'below',
        'top_breach_categories': [{'category': cat, 'count': count} for cat, count in top_categories],
        'talking_points': talking_points,
        'recent_examples': [
            {
                'ticket_id': b['ticket_id'],
                'date': b['created_ist'],
                'channel': b['channel'],
                'category': b['category'],
                'response_mins': b['response_mins'],
                'threshold_mins': b['threshold_mins'],
            }
            for b in recent_breaches[:5]
        ],
    }


def generate_all_conversation_packs(breach_results: Dict, min_breaches: int = 20) -> List[Dict]:
    """Generate conversation packs for all agents with significant breaches."""
    packs = []
    for agent_id, data in breach_results['by_agent'].items():
        if data['breached'] >= min_breaches and data['tier'] == '1':
            pack = generate_conversation_pack(agent_id, breach_results)
            packs.append(pack)
    
    # Sort by breach count descending
    packs.sort(key=lambda p: p['total_breaches'], reverse=True)
    return packs


def generate_weekly_summary(breach_results: Dict, week: str) -> Dict:
    """Generate a natural-language weekly summary."""
    week_data = breach_results['by_week'].get(week, {'breached': 0, 'total': 0})
    
    if week_data['total'] == 0:
        return {'week': week, 'summary': 'No data for this week.'}
    
    rate = week_data['breached'] / week_data['total'] * 100
    
    # Get shift breakdown
    shift_breakdown = {}
    for shift_name in ['Morning', 'Day', 'Night']:
        sw_key = f"{shift_name}|{week}"
        sw_data = breach_results['by_shift_week'].get(sw_key, {'breached': 0, 'total': 0})
        if sw_data['total'] > 0:
            shift_breakdown[shift_name] = {
                'breached': sw_data['breached'],
                'total': sw_data['total'],
                'rate': round(sw_data['breached'] / sw_data['total'] * 100, 1),
            }
    
    # Top breaching agents this week
    agent_breaches = []
    for key, data in breach_results['by_agent_week'].items():
        parts = key.split('|')
        if parts[1] == week and data['breached'] > 0:
            agent_info = breach_results['by_agent'].get(parts[0], {})
            agent_breaches.append({
                'agent_id': parts[0],
                'name': agent_info.get('name', 'Unknown'),
                'breached': data['breached'],
                'total': data['total'],
            })
    agent_breaches.sort(key=lambda x: x['breached'], reverse=True)
    
    # Build summary text
    summary = f"Week {week}: {week_data['breached']} breaches out of {week_data['total']} tickets ({rate:.0f}% breach rate). "
    
    if shift_breakdown:
        worst_shift = max(shift_breakdown.items(), key=lambda x: x[1]['rate'])
        summary += f"{worst_shift[0]} shift was worst at {worst_shift[1]['rate']}%. "
    
    if agent_breaches:
        top3 = agent_breaches[:3]
        names = ', '.join(f"{a['name']} ({a['breached']})" for a in top3)
        summary += f"Top breaching agents: {names}."
    
    return {
        'week': week,
        'total_tickets': week_data['total'],
        'total_breaches': week_data['breached'],
        'breach_rate': round(rate, 1),
        'shift_breakdown': shift_breakdown,
        'top_agents': agent_breaches[:10],
        'summary': summary,
    }
