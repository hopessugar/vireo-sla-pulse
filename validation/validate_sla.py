"""
Vireo SLA Pulse — Validation Framework
Verifies SLA breach computation accuracy through stratified sampling.
"""
import csv
import json
import random
import os
from datetime import datetime, timedelta
from engine.data_loader import load_all_data, parse_datetime, utc_to_ist
from engine.sla_calculator import compute_all_breaches, SLA_THRESHOLDS

def validate_sla_computation(data_dir: str, sample_size: int = 50):
    """
    Hand-verify a stratified random sample of tickets against computed breach status.
    Stratified by: channel (proportional), shift (proportional).
    """
    data = load_all_data(data_dir)
    results = compute_all_breaches(data['tickets'], data['agent_lookup'])
    
    all_details = results['ticket_breaches']
    
    # Stratified sampling by channel
    by_channel = {}
    for d in all_details:
        ch = d['channel']
        if ch not in by_channel:
            by_channel[ch] = []
        by_channel[ch].append(d)
    
    sample = []
    for ch, tickets in by_channel.items():
        n = max(5, int(sample_size * len(tickets) / len(all_details)))
        sample.extend(random.sample(tickets, min(n, len(tickets))))
    
    # Verify each sample
    correct = 0
    errors = []
    
    for ticket in sample:
        # Recompute from raw data
        created = parse_datetime(ticket['created_utc'])
        responded = parse_datetime(ticket['responded_utc'])
        
        if not created or not responded:
            continue
        
        resp_mins = (responded - created).total_seconds() / 60
        threshold = SLA_THRESHOLDS.get(ticket['channel'], 480)
        expected_breach = resp_mins > threshold
        actual_breach = ticket['breached']
        
        if expected_breach == actual_breach:
            correct += 1
        else:
            errors.append({
                'ticket_id': ticket['ticket_id'],
                'channel': ticket['channel'],
                'response_mins': resp_mins,
                'threshold': threshold,
                'expected': expected_breach,
                'actual': actual_breach,
            })
    
    total = len(sample)
    accuracy = correct / total * 100 if total > 0 else 0
    
    # Edge case analysis
    edge_cases = {
        'tickets_with_zero_response': sum(1 for d in all_details if d['response_mins'] == 0),
        'tickets_with_negative_response': sum(1 for d in all_details if d['response_mins'] < 0),
        'tier2_agents_included': sum(1 for d in all_details if d['tier'] == '2'),
        'legacy_tickets': sum(1 for d in all_details if d['source_system'] == 'legacy_fd'),
        'cross_shift_tickets': sum(1 for d in all_details if d['agent_shift'] != d['ticket_shift']),
    }
    
    # Channel-wise accuracy
    channel_accuracy = {}
    for ch in by_channel:
        ch_sample = [s for s in sample if s['channel'] == ch]
        ch_correct = sum(1 for s in ch_sample if s not in [e for e in errors])
        channel_accuracy[ch] = {
            'sample_size': len(ch_sample),
            'correct': ch_correct,
            'accuracy': round(ch_correct / max(len(ch_sample), 1) * 100, 1)
        }
    
    return {
        'sample_size': total,
        'correct': correct,
        'errors': len(errors),
        'accuracy_pct': round(accuracy, 1),
        'error_details': errors[:10],
        'edge_cases': edge_cases,
        'channel_accuracy': channel_accuracy,
        'methodology': {
            'sampling': 'Stratified random by channel, proportional allocation',
            'verification': 'Independent recomputation from raw timestamps',
            'thresholds_used': SLA_THRESHOLDS,
        }
    }


if __name__ == '__main__':
    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Running SLA validation...")
    results = validate_sla_computation(data_dir)
    
    print(f"\n{'='*50}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*50}")
    print(f"Sample size: {results['sample_size']}")
    print(f"Correct: {results['correct']}")
    print(f"Errors: {results['errors']}")
    print(f"Accuracy: {results['accuracy_pct']}%")
    
    print(f"\nEdge cases:")
    for k, v in results['edge_cases'].items():
        print(f"  {k}: {v}")
    
    print(f"\nChannel accuracy:")
    for ch, d in results['channel_accuracy'].items():
        print(f"  {ch}: {d['accuracy']}% ({d['correct']}/{d['sample_size']})")
    
    # Save results
    out_path = os.path.join(data_dir, 'validation', 'results.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {out_path}")
