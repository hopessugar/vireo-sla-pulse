"""
Vireo SLA Pulse — Data Loader
Handles all CSV loading, cleaning, deduplication, and timezone conversion.
"""
import csv
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

IST_OFFSET = timedelta(hours=5, minutes=30)


def find_file(data_dir: str, pattern: str) -> str:
    """Find a file in data_dir matching the pattern, handling UUID-prefixed filenames."""
    # Try exact match first
    exact = os.path.join(data_dir, pattern)
    if os.path.exists(exact):
        return exact
    # Try glob with UUID prefix
    matches = glob.glob(os.path.join(data_dir, f"*{pattern}"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Cannot find {pattern} in {data_dir}")


def load_csv(filepath: str) -> List[Dict]:
    """Load a CSV file and return list of dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse a datetime string, returning None on failure."""
    if not dt_str or not dt_str.strip():
        return None
    dt_str = dt_str.strip()
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def utc_to_ist(dt: datetime) -> datetime:
    """Convert UTC datetime to IST (UTC+5:30)."""
    return dt + IST_OFFSET


def deduplicate_tickets(tickets: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Deduplicate tickets by ticket_id.
    Per Sameer: re-imported during migration may appear twice.
    Keep the last occurrence (most recent data).
    Returns (deduped_list, num_removed).
    """
    seen = {}
    for t in tickets:
        seen[t['ticket_id']] = t
    deduped = list(seen.values())
    return deduped, len(tickets) - len(deduped)


def normalize_csat(tickets: List[Dict]) -> List[Dict]:
    """
    Normalize CSAT scores.
    Per policy §8 and Sameer: legacy rows use 0 for no response,
    new system uses blank. Treat both as None.
    """
    for t in tickets:
        score = t.get('csat_score', '').strip()
        if score == '' or score == '0':
            t['csat_score_normalized'] = None
        else:
            try:
                t['csat_score_normalized'] = int(score)
            except ValueError:
                t['csat_score_normalized'] = None
    return tickets


def build_agent_lookup(agents: List[Dict]) -> Dict:
    """
    Build a lookup: agent_id -> list of assignments sorted by from_date.
    Each assignment has shift, site, team, name, from_date, to_date.
    """
    lookup = {}
    for a in agents:
        aid = a['agent_id']
        if aid not in lookup:
            lookup[aid] = {
                'name': a['name'],
                'assignments': []
            }
        
        from_dt = parse_datetime(a.get('from_date', ''))
        to_dt = parse_datetime(a.get('to_date', ''))
        
        lookup[aid]['assignments'].append({
            'shift': a['shift'],
            'site': a['site'],
            'team': a['team'],
            'tier': a.get('tier', '1'),
            'from_date': from_dt or datetime.min,
            'to_date': to_dt or datetime.max,
        })
    
    # Sort assignments by from_date
    for aid in lookup:
        lookup[aid]['assignments'].sort(key=lambda x: x['from_date'])
    
    return lookup


def get_agent_info_at_date(agent_lookup: Dict, agent_id: str, dt: datetime) -> Dict:
    """
    Get agent's shift/site/team at a specific date.
    Uses temporal join per roster's from/to date ranges.
    """
    if agent_id not in agent_lookup:
        return {
            'name': 'Unknown', 'shift': 'Unknown', 'site': 'Unknown',
            'team': 'Unknown', 'tier': '1'
        }
    
    agent = agent_lookup[agent_id]
    for assignment in agent['assignments']:
        if assignment['from_date'] <= dt <= assignment['to_date']:
            return {
                'name': agent['name'],
                'shift': assignment['shift'],
                'site': assignment['site'],
                'team': assignment['team'],
                'tier': assignment['tier'],
            }
    
    # Fallback: use the latest assignment
    latest = agent['assignments'][-1]
    return {
        'name': agent['name'],
        'shift': latest['shift'],
        'site': latest['site'],
        'team': latest['team'],
        'tier': latest['tier'],
    }


def detect_ivr_failures(tickets: List[Dict]) -> List[Dict]:
    """
    Flag failed IVR transcripts per Sameer's note (~40 of them).
    Failed IVR transcripts are short garbled voice channel messages.
    """
    for t in tickets:
        msg = t.get('customer_message', '')
        is_ivr = (
            t.get('channel') == 'voice' and
            msg.startswith('[IVR transcript]') and
            (len(msg) < 50 or 'unintelligible' in msg.lower() or 'static' in msg.lower())
        )
        t['is_failed_ivr'] = is_ivr
    return tickets


def load_all_data(data_dir: str) -> Dict:
    """
    Master loader: loads all CSVs, cleans, deduplicates, normalizes.
    Returns a dict with all processed data.
    """
    # Find files (handle UUID prefixes)
    tickets_file = find_file(data_dir, 'tickets.csv')
    agents_file = find_file(data_dir, 'agents.csv')
    customers_file = find_file(data_dir, 'customers.csv')
    orders_file = find_file(data_dir, 'orders.csv')
    products_file = find_file(data_dir, 'products.csv')
    
    # Load raw data
    raw_tickets = load_csv(tickets_file)
    agents = load_csv(agents_file)
    customers = load_csv(customers_file)
    orders = load_csv(orders_file)
    products = load_csv(products_file)
    
    # Process tickets
    tickets, dups_removed = deduplicate_tickets(raw_tickets)
    tickets = normalize_csat(tickets)
    tickets = detect_ivr_failures(tickets)
    
    # Build agent lookup
    agent_lookup = build_agent_lookup(agents)
    
    # Build product lookup
    product_lookup = {p['sku']: p for p in products}
    
    return {
        'tickets': tickets,
        'agents_raw': agents,
        'agent_lookup': agent_lookup,
        'customers': customers,
        'orders': orders,
        'products': products,
        'product_lookup': product_lookup,
        'stats': {
            'total_raw_rows': len(raw_tickets),
            'duplicates_removed': dups_removed,
            'total_clean_tickets': len(tickets),
        }
    }
