"""
Vireo SLA Pulse — FastAPI Server
Serves the dashboard and all API endpoints for breach data.
"""
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from engine.data_loader import load_all_data
from engine.sla_calculator import compute_all_breaches, compute_financial_impact
from ai.classifier import (
    detect_breach_patterns,
    generate_all_conversation_packs,
    generate_conversation_pack,
    generate_weekly_summary,
    validate_categories,
)

app = FastAPI(title="Vireo SLA Pulse", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global state (computed on startup) ──────────────────────────────────────
DATA = {}
BREACH_RESULTS = {}
FINANCIAL = {}
PATTERNS = []
CONVERSATION_PACKS = []
VALIDATION = {}


@app.on_event("startup")
def startup():
    global DATA, BREACH_RESULTS, FINANCIAL, PATTERNS, CONVERSATION_PACKS, VALIDATION
    
    data_dir = os.environ.get("DATA_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"[Vireo SLA Pulse] Loading data from: {data_dir}")
    
    DATA = load_all_data(data_dir)
    print(f"[Vireo SLA Pulse] Loaded {DATA['stats']['total_clean_tickets']} tickets "
          f"(removed {DATA['stats']['duplicates_removed']} duplicates)")
    
    BREACH_RESULTS = compute_all_breaches(DATA['tickets'], DATA['agent_lookup'])
    print(f"[Vireo SLA Pulse] Computed breaches: {BREACH_RESULTS['summary']['total_breached']} / "
          f"{BREACH_RESULTS['summary']['total_valid']} = "
          f"{BREACH_RESULTS['summary']['total_breached']/max(BREACH_RESULTS['summary']['total_valid'],1)*100:.1f}%")
    
    FINANCIAL = compute_financial_impact(BREACH_RESULTS)
    print(f"[Vireo SLA Pulse] Financial impact: Rs {FINANCIAL['total_credits_18m']:,} total credits")
    
    PATTERNS = detect_breach_patterns(BREACH_RESULTS)
    print(f"[Vireo SLA Pulse] Detected {len(PATTERNS)} breach patterns")
    
    CONVERSATION_PACKS = generate_all_conversation_packs(BREACH_RESULTS, min_breaches=15)
    print(f"[Vireo SLA Pulse] Generated {len(CONVERSATION_PACKS)} conversation packs")
    
    VALIDATION = validate_categories(DATA['tickets'])
    print(f"[Vireo SLA Pulse] Category validation: {VALIDATION['accuracy']}% accuracy")
    
    print("[Vireo SLA Pulse] READY")


# ─── Dashboard ───────────────────────────────────────────────────────────────

dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/static", StaticFiles(directory=dashboard_dir), name="static")


@app.get("/")
def serve_dashboard():
    index_path = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Vireo SLA Pulse API is running. Dashboard not found."}


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/summary")
def get_summary():
    """Overall breach summary with key metrics."""
    s = BREACH_RESULTS['summary']
    return {
        "total_tickets_analyzed": s['total_valid'],
        "total_breached": s['total_breached'],
        "total_met_sla": s['total_met'],
        "breach_rate_pct": round(s['total_breached'] / max(s['total_valid'], 1) * 100, 1),
        "total_credits_inr": s['total_credits_inr'],
        "skipped_open_pending": s['skipped_open_pending'],
        "duplicates_removed": DATA['stats']['duplicates_removed'],
        "financial": FINANCIAL,
    }


@app.get("/api/by-shift")
def get_by_shift():
    """Breach data grouped by shift."""
    result = {}
    for shift, data in BREACH_RESULTS['by_shift'].items():
        total = data['total']
        breached = data['breached']
        result[shift] = {
            "total": total,
            "breached": breached,
            "met_sla": total - breached,
            "breach_rate": round(breached / max(total, 1) * 100, 1),
            "avg_response_mins": round(sum(data['resp_times']) / max(len(data['resp_times']), 1), 1),
        }
    return result


@app.get("/api/by-channel")
def get_by_channel():
    """Breach data grouped by channel."""
    result = {}
    for channel, data in BREACH_RESULTS['by_channel'].items():
        total = data['total']
        breached = data['breached']
        result[channel] = {
            "total": total,
            "breached": breached,
            "met_sla": total - breached,
            "breach_rate": round(breached / max(total, 1) * 100, 1),
            "threshold_mins": data['threshold'],
            "avg_response_mins": round(sum(data['resp_times']) / max(len(data['resp_times']), 1), 1),
        }
    return result


@app.get("/api/by-agent")
def get_by_agent():
    """Breach data for all agents, sorted by breach count."""
    agents = []
    for aid, data in BREACH_RESULTS['by_agent'].items():
        agents.append({
            "agent_id": aid,
            "name": data['name'],
            "shift": data['shift'],
            "site": data['site'],
            "team": data['team'],
            "tier": data['tier'],
            "total": data['total'],
            "breached": data['breached'],
            "breach_rate": data['breach_rate'],
            "avg_response_mins": data['avg_resp_mins'],
            "p50_response_mins": data['p50_resp_mins'],
            "p90_response_mins": data['p90_resp_mins'],
            "top_breach_categories": dict(
                sorted(data['breach_categories'].items(), key=lambda x: x[1], reverse=True)[:3]
            ),
        })
    agents.sort(key=lambda a: a['breached'], reverse=True)
    return agents


@app.get("/api/weekly-trend")
def get_weekly_trend():
    """Weekly breach trend with shift breakdown."""
    return BREACH_RESULTS.get('weekly_trend', [])


@app.get("/api/by-category")
def get_by_category():
    """Breach data grouped by ticket category."""
    result = {}
    for cat, data in BREACH_RESULTS['by_category'].items():
        total = data['total']
        breached = data['breached']
        result[cat] = {
            "total": total,
            "breached": breached,
            "breach_rate": round(breached / max(total, 1) * 100, 1),
        }
    return result


@app.get("/api/heatmap")
def get_heatmap():
    """Breach heatmap data: hour × day-of-week."""
    result = []
    for key, data in BREACH_RESULTS['by_hour_dow'].items():
        parts = key.split('|')
        dow = parts[0]
        hour = int(parts[1])
        total = data['total']
        breached = data['breached']
        result.append({
            "day": dow,
            "hour": hour,
            "total": total,
            "breached": breached,
            "rate": round(breached / max(total, 1) * 100, 1),
        })
    return result


@app.get("/api/patterns")
def get_patterns():
    """Detected breach patterns."""
    return PATTERNS


@app.get("/api/conversation-packs")
def get_conversation_packs():
    """All agent conversation packs for 1:1 meetings."""
    return CONVERSATION_PACKS


@app.get("/api/conversation-pack/{agent_id}")
def get_conversation_pack(agent_id: str):
    """Conversation pack for a specific agent."""
    pack = generate_conversation_pack(agent_id, BREACH_RESULTS)
    if 'error' in pack:
        raise HTTPException(status_code=404, detail=pack['error'])
    return pack


@app.get("/api/weekly-report/{week}")
def get_weekly_report(week: str):
    """Detailed report for a specific week."""
    report = generate_weekly_summary(BREACH_RESULTS, week)
    return report


@app.get("/api/weeks")
def get_weeks():
    """List all available weeks."""
    return sorted(BREACH_RESULTS['by_week'].keys())


@app.get("/api/validation")
def get_validation():
    """AI classification validation results."""
    return VALIDATION


@app.get("/api/financial")
def get_financial():
    """Financial impact analysis."""
    return FINANCIAL
