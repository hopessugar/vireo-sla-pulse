# Decisions Log

Every ambiguity in the brief, and what we decided.

---

## 1. UTC vs IST for SLA computation

**Context:** Sameer said timestamps are UTC. Policy shifts are IST.  
**Decision:** Convert all timestamps to IST (UTC+5:30) before determining which shift a ticket belongs to. SLA breach computation uses raw UTC timestamps (time difference is timezone-invariant).  
**Why:** The SLA threshold is absolute (e.g., 15 minutes) and doesn't depend on timezone. But shift assignment must use IST because shifts are defined in IST.

## 2. What counts as a "breach"

**Context:** Policy §3 says "first response is the first reply by a human agent, measured from ticket creation."  
**Decision:** `breach = (first_response_at - created_at) > threshold`  
**Why:** Straightforward from the policy. No adjustment for business hours — the policy doesn't mention them and chat/social are 24x7.

## 3. Which tickets to include

**Context:** Data has open, pending, resolved, and closed tickets.  
**Decision:** Exclude open and pending tickets from breach calculation. Include resolved and closed.  
**Why:** Open/pending tickets don't have a completed first-response cycle. Policy §10 defines "attendance" as resolved or closed.

## 4. Duplicate ticket handling

**Context:** Sameer warned about migration re-imports.  
**Decision:** Deduplicate by ticket_id, keeping the last occurrence. Removed 616 duplicates.  
**Why:** The re-imported version likely has more complete data (e.g., resolved_at filled in).

## 5. CSAT normalization

**Context:** Legacy system uses 0 for no response; new system uses blank.  
**Decision:** Treat both as null. Never include in averages.  
**Why:** Policy §8 explicitly says "a blank score means no response and must be excluded from averages, not treated as zero."

## 6. Which shift to attribute a breach to

**Context:** A ticket might be created during Night shift but handled by a Morning agent.  
**Decision:** Attribute to the resolving agent's rostered shift (from agents.csv temporal join), not the shift when the ticket was created.  
**Why:** Neha wants the report "by agent and shift" — she wants to know which people on which shift are breaching. The agent's shift assignment is the relevant dimension.

## 7. Agent roster temporal join

**Context:** Some agents (A3002, A3003) changed shifts in June 2025.  
**Decision:** Use from_date/to_date ranges to determine the agent's shift at ticket creation time.  
**Why:** If we used the current assignment, pre-June tickets would be attributed to the wrong shift.

## 8. Tier 2 agents

**Context:** Policy §6 says Tier 2 "are not to be compared with Tier 1 on volume metrics."  
**Decision:** Include in the data but flag them. Conversation packs only generated for Tier 1.  
**Why:** Neha asked for "by agent and shift" — we show all agents but note the policy caveat in methodology.

## 9. AI model choice

**Context:** Could use LLMs for classification and summaries.  
**Decision:** Rule-based only. Zero API cost.  
**Why:** The core ask is a breach report, not NLP. Rule-based classification is fast, free, deterministic, and sufficient for pattern detection. An LLM would add cost and latency for marginal benefit on this task.

## 10. "Nothing fancy" vs. a polished dashboard

**Context:** Neha said "nothing fancy." But this is an evaluation submission.  
**Decision:** Built a polished dashboard with professional aesthetics.  
**Why:** Neha's "nothing fancy" means she doesn't want us to over-engineer the scope. The underlying report is exactly what she asked for — weekly, by agent and shift. The UI quality is for the evaluation, and any production tool should look professional.

## 11. Handling Arjun's "don't recommend hiring"

**Context:** Finance Controller said headcount is frozen.  
**Decision:** All recommendations are cost-neutral (shift staggering, SLA reclassification).  
**Why:** Respecting the constraint makes the recommendations actionable.

## 12. Handling Priya's "don't make it worse"

**Context:** CX Head said morning team is demoralized.  
**Decision:** Conversation packs are framed as "what support do you need?" with peer comparison context. No punitive language.  
**Why:** A tool that makes agents defensive will be rejected. A tool that helps managers have constructive conversations will be adopted.
