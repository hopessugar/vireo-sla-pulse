# Memo: First-Response SLA Breach Report

**To:** Neha Kulkarni, Support Operations Manager  
**From:** Vireo SLA Pulse (automated analysis)  
**Date:** October 2026  
**Re:** Weekly breach report findings and recommendations  

---

## The headline

**One in five tickets (21.9%) breaches first-response SLA.** Nearly all of the problem sits in the Morning shift, which breaches at 32.3% — four times the Day shift's 8.5%. This has cost Rs 8.12 lakh in automatic store credits over 18 months and is the main driver of the SLA credit line Arjun flagged.

---

## Where the breaches are

| Shift | Breach Rate | Tickets | Credits Issued |
|-------|-------------|---------|----------------|
| **Morning** | **32.3%** | 5,928 | **Rs 6.71L** |
| Day | 8.5% | 4,428 | Rs 1.32L |
| Night | 10.6% | 255 | Rs 0.09L |

The morning shift runs 20 agents across Bengaluru and Indore. Every one of the top 15 breaching agents is on the morning shift. This is not an individual performance problem — it is a structural one.

**Chat is the hardest-hit channel** at 27.6% breach rate. The 15-minute SLA for chat is tight, and when agents start their shift they inherit a queue of overnight tickets that are already past SLA. Priya is right: the morning team opens to a wall of red because those tickets were already breached before they sat down.

---

## Why it's happening

The overnight period (22:00–06:00) is covered by 3–5 Indore night-shift agents handling chat, email, and social. When ticket volume peaks between 23:00 and 05:00 IST, the queue backs up. By the time the morning shift logs in at 06:00, there are tickets already 2–6 hours old in a channel with a 15-minute SLA.

**The breach is baked in before the morning shift starts.** The agents are not slow — the queue is pre-breached.

---

## The money

- **Rs 8.12 lakh** in SLA credits issued over 18 months (Rs 350 per breach, automatic)
- **Rs 1.35 lakh per quarter** at the current rate
- **Rs 4.95 lakh is avoidable** if Morning shift breach rate matched Day's 8.5%
- That is roughly **Rs 82,500 per quarter** in savings — without hiring anyone

Arjun noted the SLA credit line has tripled. The data confirms it: helpdesk-era tickets (post Sep 2025) show higher breach counts, likely because the new system enforces the 15-minute chat SLA more strictly than Freshdesk did.

---

## What can be done (within frozen headcount)

1. **Stagger one morning agent to start at 05:00 IST** to clear the overnight chat queue before the 06:00 rush. Cost-neutral — shift the end time correspondingly.

2. **Route overnight chat tickets to the email SLA** (8 hours) instead of the chat SLA (15 minutes) when no chat agent is online. The customer wrote at 2 AM; they don't expect a 15-minute reply. This alone could cut 30–40% of morning breaches.

3. **Use the Conversation Packs** in the tool. For each of the top breaching agents, the tool generates specific talking points with data, examples, and peer comparisons — framed around "what support do you need?" not "why did you fail?"

4. **Track weekly, act monthly.** The dashboard shows breach trends by shift and agent, week over week. Use the trend to spot whether interventions are working.

---

## What this tool does

The Vireo SLA Pulse dashboard:
- Computes first-response breaches for every ticket using policy thresholds
- Breaks down by agent, shift, channel, category, and week
- Generates conversation packs for 1:1 meetings with specific agents
- Detects systemic patterns (e.g., overnight queue, category clusters)
- Calculates financial impact in rupees

It runs on a single command (`python run.py`), costs nothing to operate, and needs no external APIs.

---

*This memo is 1 page (~5 minutes to read). *
