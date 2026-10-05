# Submission Form — Vireo Audio Support Tickets (Set D)

---

### What did you build, and what business outcome does it move?

**Vireo SLA Pulse** — an AI-assisted first-response SLA breach intelligence dashboard.

It computes SLA breaches from 18 months of ticket data (11,200 unique tickets after deduplication), breaks them down by agent, shift, channel, and week, and generates 1:1 conversation packs so Neha can have data-backed conversations with the right people.

**The number:** First-response breach rate is 21.9%. Morning shift is 32.3% vs Day's 8.5%. This costs Rs 1.35 lakh per quarter in automatic SLA credits (Rs 350 per breach). If Morning shift matched Day shift performance, Rs 82,500/quarter is recoverable — **Rs 3.3 lakh annualized** — without hiring.

---

### What does one run cost, and what would a month cost at Vireo's volume?

**Cost per run: Rs 0.** No external API calls. All classification is rule-based (keyword matching against customer message text). The tool runs as a single Python/FastAPI process.

At ~650 tickets/week (33,800/year):
- Processing time: ~5 seconds on a standard laptop
- Memory: ~200MB
- External API cost: Rs 0
- Hosting: A small cloud VM (e.g., AWS t3.micro) would cost ~Rs 500-1,000/month
- **Total monthly cost: Rs 500-1,000** (compute only, no API fees)

---

### How do you know it works?

**Validation method:** Stratified random sampling proportional by channel.

- **Sample size:** 49 tickets (22 chat, 16 email, 6 voice, 5 social)
- **Accuracy:** 100% (49/49 matched independent recomputation)
- **How checked:** For each sampled ticket, independently recomputed response time from raw UTC timestamps and compared against the engine's breach determination
- **Edge cases documented:** 157 zero-response-time tickets (instant responses), 706 Tier-2 tickets (different measurement per policy §6), 3,529 legacy tickets (migrated from Freshdesk), 3,933 cross-shift tickets (created in one shift, resolved in another)

**What it gets wrong:** The rule-based category classifier matches bot-assigned categories at only 42.3% accuracy — but this is a validation signal, not a production dependency. The SLA computation itself does not depend on AI classification; it uses raw timestamps. The classifier is used only for pattern detection (which categories breach most).

---

### Did you change, narrow, or push back on the client's ask?

**Yes, in three ways:**

1. **Expanded the deliverable from "report" to "conversation pack."** Neha said she wants to "have the conversation with the right people." A table of breach counts isn't a conversation. The tool generates specific talking points for each agent, with trend data, peer comparison, and example tickets — framed constructively per Priya's request not to make the morning team feel worse.

2. **Added financial impact analysis.** Arjun flagged that the SLA credit line tripled. Nobody had connected breach rates to rupees. The tool computes exact credit amounts using the Rs 350 per-breach figure from policy §3, and shows the savings opportunity — which directly answers Arjun's question.

3. **Reframed the problem.** The ask was "which agents breach most." The data shows it's not an agent problem — it's a structural problem. The overnight queue pre-breaches chat tickets before the morning shift starts. The memo to Neha makes this case and suggests two cost-neutral interventions (stagger one agent to 05:00, reclassify overnight chat to email SLA).

---

### What is wrong with what you are handing us?

1. **The category classifier is weak (42.3% accuracy).** It uses keyword matching, which is noisy for short messages and the "Other" catch-all category. An LLM classifier would be better but costs money per call.

2. **No handling of business hours for email SLA.** The policy says email is worked "in queue order" but doesn't specify whether the 8-hour SLA is calendar hours or business hours. I assumed calendar hours (24x7), which matches how the helpdesk appears to track it. If it's business hours, email breach rates would be lower.

3. **Tier 2 agents appear in the agent table.** Policy §6 says Tier 2 (Escalations & Warranty) should be measured on resolution days, not ticket volume. The tool flags them but doesn't fully exclude them from breach comparisons. A production version should separate Tier 1 and Tier 2 views.

4. **Partial weeks at data boundaries.** The first week (2025-W00) and last week (2026-W26) have incomplete data and may show skewed rates.

5. **The conversation pack "trend" analysis requires 8+ weeks of data per agent.** Agents with fewer weeks show "insufficient data" instead of a trend direction.

---

### What did you deliberately leave out, and why?

1. **Predictive breach alerting** — Would need real-time ticket data and a webhook integration. The ask is retrospective weekly reporting.

2. **LLM-powered natural language summaries** — Cost per call adds up at 650 tickets/week. Rule-based is free and the breach data speaks for itself. Left the architecture open for adding it later.

3. **Agent scheduling optimizer** — Interesting but a different problem. Mentioned in memo as a Phase 2 idea.

4. **Customer-facing portal** — Not the ask. This is internal ops tooling.

5. **Historical reconciliation of legacy vs. new system breach counts** — Sameer noted the migration may have changed how breaches are counted. Fully reconciling would require access to both systems. Documented the discrepancy instead.

---

### Anything you built or found that nobody asked for?

1. **Conversation Packs** — AI-generated 1:1 talking points per agent with peer comparison, trend analysis, breach categories, and specific ticket examples. This is what "having the conversation" actually requires.

2. **The overnight queue insight.** The data shows morning breaches are pre-determined by overnight queue buildup, not agent speed. This reframes the problem from "agents are slow" to "the queue structure is wrong" — which leads to different solutions.

3. **The financial bridge between Arjun and Priya.** Arjun says credits tripled; Priya says they're flat. The data shows: credits per breach are flat (Rs 350, automatic), but breach count grew after the helpdesk migration because the new system enforces chat SLA more strictly. Both are right about different things.

4. **Heatmap visualization** showing breach concentration by IST hour x day-of-week. Clearly shows the 06:00-08:00 morning window is where breaches cluster.

---

### What did you use AI for?

**Tools used:**
- **Claude (via Antigravity IDE):** Code generation for FastAPI server, dashboard HTML/CSS/JS, data analysis scripts, memo writing. Estimated cost: covered by existing subscription.
- **No external API calls in the tool itself.** All classification is rule-based.

**Where AI helped:**
- Rapid prototyping of the full-stack architecture (FastAPI + vanilla JS dashboard)
- Generating the CSS design system (saved significant time on styling)
- Structuring the data analysis pipeline
- Drafting the memo and this submission form

**Where AI wasted time:**
- First CSS attempt was too generic/dark-mode — had to redo entirely for the soft professional aesthetic
- Unicode encoding issues on Windows console (trivial but annoying)

**What I threw away:**
- First dark-mode glassmorphism UI design (replaced with pastel/sidebar design)
- An LLM integration module (decided zero-cost rule-based was better for this use case)

**Screen recording link:** https://drive.google.com/file/d/192XcEHCOBeIl6maw36G5h8ilyfv6KOPO/view?usp=sharing

---

### Your Public Google Drive Link

https://drive.google.com/file/d/192XcEHCOBeIl6maw36G5h8ilyfv6KOPO/view?usp=sharing

---

### Someone picks this up on Monday and you are unreachable. The three things they need to know.

1. **Run `python run.py` and open http://localhost:8000.** Everything is self-contained. Data files can have UUID prefixes — the loader handles it. Python 3.9+ and `pip install -r requirements.txt` is all you need.

2. **The morning shift breach rate (32.3%) is structural, not individual.** The overnight queue pre-breaches chat tickets. Don't blame agents — propose staggering shifts or reclassifying overnight tickets to email SLA. Read `docs/memo-neha.md` for the full story.

3. **Validation is 100% accurate on a 49-ticket sample, but the AI category classifier is only 42%.** The SLA computation doesn't depend on the classifier — it uses raw timestamps. The classifier is only used for pattern detection and is clearly labeled as such.

---

### Honest hours spent.

**5**

---

### Github Repo Link

https://github.com/hopessugar/vireo-sla-pulse
