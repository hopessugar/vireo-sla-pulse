# Vireo SLA Pulse

**First-response SLA breach intelligence for Vireo Audio's support desk.**

A self-contained tool that computes SLA breaches from ticket exports, identifies which agents and shifts breach most, and generates weekly reports with actionable conversation packs for 1:1s.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place your data files in this directory
#    Required: tickets.csv, agents.csv, customers.csv, orders.csv, products.csv
#    (UUID-prefixed filenames from exports are handled automatically)

# 3. Run
python run.py

# 4. Open
#    Dashboard: http://localhost:8000
#    API docs:  http://localhost:8000/docs
```

**Requirements:** Python 3.9+, pip. No external API keys needed.

---

## What It Does

1. **Loads & cleans** 18 months of ticket data (deduplicates, normalizes CSAT, converts UTC->IST)
2. **Computes SLA breaches** per channel thresholds (Chat: 15min, Voice: 2hr, Social: 4hr, Email: 8hr)
3. **Maps agents to shifts** using temporal roster join (handles mid-period reassignments)
4. **Generates weekly breach reports** by agent x shift, with drill-down
5. **Detects breach patterns** (which shift x channel x category clusters)
6. **Produces conversation packs** — 1:1 talking points per agent with specific examples
7. **Calculates financial impact** — total credits, quarterly cost, savings opportunity

---

## Dashboard Tabs

| Tab | What it shows |
|-----|--------------|
| **Dashboard** | KPIs with circular progress, shift/channel charts, 18-month trend, heatmap |
| **Agents** | Sortable/searchable table of all 44 agents with breach rates |
| **Weekly Trends** | Shift-by-shift weekly breakdown with drill-down |
| **Conversation Packs** | Expandable 1:1 talking points for each breaching agent |
| **Patterns** | AI-detected breach clusters (shift x channel, category, day-of-week) |
| **Financial Impact** | Money numbers: Rs 8.12L total credits, savings opportunity |
| **Methodology** | How everything was computed, edge cases, validation results |

---

## Key Findings

- **21.9% overall breach rate** (2,320 of 10,611 tickets)
- **Morning shift: 32.3%** vs Day: 8.5% — the gap is systemic, not individual
- **Chat channel worst** at 27.6% (15-min SLA is tight with overnight queue buildup)
- **All top 15 breaching agents are Morning shift**
- **Rs 8.12L in SLA credits** over 18 months (Rs 1.35L/quarter)
- **Rs 4.95L avoidable** if Morning matched Day shift performance

---

## Architecture

```
vireo-sla-pulse/
├── run.py                  # Entry point: python run.py
├── requirements.txt        # fastapi, uvicorn
├── engine/
│   ├── data_loader.py      # CSV loading, dedup, CSAT normalization, UTC->IST
│   └── sla_calculator.py   # Core SLA computation, financial model
├── ai/
│   └── classifier.py       # Rule-based classification, pattern detection, conversation packs
├── api/
│   └── server.py           # FastAPI server (12 endpoints)
├── dashboard/
│   ├── index.html           # Single-page app with sidebar navigation
│   ├── css/design-system.css
│   └── js/app.js
└── validation/
    ├── validate_sla.py      # Stratified sample validation
    └── results.json         # Published results (100% accuracy, n=49)
```

---

## Data Quality Decisions

| Issue | Decision | Source |
|-------|----------|--------|
| Timestamps are UTC | Convert to IST before shift assignment | Sameer's email |
| Duplicate ticket_ids | Deduplicate, keep last occurrence (616 removed) | Sameer's email |
| CSAT score 0 in legacy | Treat as null (no response), not a rating | Policy §8, Sameer |
| ~40 failed IVR transcripts | Included (valid timestamps, flagged) | Sameer's email |
| Agents with date ranges | Temporal join on from/to dates | Policy §7 |
| June 2025 Indore reshuffle | Correctly maps pre/post shift via temporal join | Neha's email |

---

## Validation

- **Method:** Stratified random sample (proportional by channel)
- **Sample size:** 49 tickets
- **Accuracy:** 100% (49/49 correct)
- **Channels verified:** Chat (22), Email (16), Voice (6), Social (5)
- **Edge cases documented:** 157 zero-response-time tickets, 706 Tier-2 tickets, 3,529 legacy tickets

---

## Cost

- **API cost:** Rs 0 (zero external API calls — all classification is rule-based)
- **Running cost:** Compute only (single Python process, ~200MB RAM)
- **At Vireo's volume (~650 tickets/week):** No incremental cost per run
- **Monthly estimated cost:** Rs 0 for the tool itself; hosting a small VM would be ~Rs 500-1,000/month

---

## What's Not Included (and why)

- **Predictive breach model:** The ask is a retrospective report, not a forecast
- **Real-time monitoring:** Would need webhook integration; the ask is weekly
- **Agent scheduling optimizer:** Adjacent problem, would be scope creep
- **LLM-generated summaries:** Added cost for marginal benefit; rule-based is sufficient and free
