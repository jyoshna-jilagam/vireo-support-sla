## Methodology

### Source rules (from the supplied files)
- First response is the first human reply, measured from ticket creation (policy section 3).
- Targets: chat 15 minutes, voice callback 2 hours, social 4 hours, email 8 hours.
- A breach is a first response later than the target (policy section 10). A reply exactly on the target is not a breach.
- Each breach issues a Rs 350 store credit on resolution, regardless of cause (policy section 3).
- Shifts are defined in IST: Morning 06:00-14:00, Day 14:00-22:00, Night 22:00-06:00 (policy section 7).
- The helpdesk API export is in UTC (email thread, data README).

### Calculations
| Item | Rule |
|---|---|
| Response time | first_response_at minus created_at, in minutes (both UTC, so no conversion needed) |
| Breach | response time greater than the channel target |
| Local time | UTC plus 5 hours 30 minutes |
| Week | Monday to Sunday, based on the IST creation date |
| Agent | agent_id on the ticket, which is the resolving agent. The policy says breaches are reported against this agent |
| Arrival shift | shift containing the IST creation time |
| Rostered shift | the agent's roster row whose from_date/to_date covers the IST creation date |
| Credit | Rs 350 for breached tickets with status resolved or closed. Open and pending tickets have no credit yet |

### Decisions on ambiguous points
1. **Duplicates.** 616 ticket ids appear twice (legacy_fd and helpdesk copies). All fields except source_system and csat_score are identical, so one copy is kept (helpdesk). 11,816 rows become 11,200 tickets.
2. **Two shift views.** "Shift" can mean the arrival shift or the resolving agent's rostered shift. Both are shown. The arrival shift is the primary view because the data shows the pattern follows when tickets arrive.
3. **Agent attribution.** The export holds only the resolving agent. Who sent the first reply is not recorded. Where those differ, agent figures are approximate. This is a limitation and is stated in the memo.
4. **Ranking.** Agents are shown with ticket counts and a Wilson 95 percent interval. Rows with fewer than 30 tickets are flagged and not ranked. A second agent rate excludes overnight arrivals.
5. **Period split.** 30 June 2025 is used as a split point because the roster shows the Night assignments ending on 29 June 2025.
6. **Cost.** Only the Rs 350 credit is used, since the policy states it. The cost of extra cover is not netted off because headcount is frozen and the amount of reassigned time is not in the data.

### Volume check
The export holds about 176 tickets a week over the last 26 weeks. The client quoted roughly 650 a week. We do not know whether the export is a sample, so rupee figures are reported for the export only. If it is a sample covering about 27 percent of volume, the quarterly figures would scale by about 3.7 times. This is a sensitivity, not a finding.

### Out of scope
- CSAT analysis (mentioned in the email thread, not requested).
- Orders, customers and products tables: they do not affect a first-response SLA.
- Refund and replacement checks, and handle time.
- Using a language model to compute anything. All numbers come from deterministic code.

### Validation
- Data quality checks: duplicates, missing and impossible timestamps, unknown agents, missing roster rows, channels without a target.
- Ten unit tests with fixed inputs: boundary minutes, channel targets, UTC to IST, shift boundaries, Monday week start across midnight IST, duplicate handling, credit rules, interval width, and a sample of the real data.
- Independent recomputation of 500 random tickets with plain Python from the raw CSV. It compares breach, week, arrival shift and rostered shift.
- Weekly counts are checked to add back to the ticket-level totals.

This validates the implementation. It cannot prove the policy was interpreted as the client intended. The main interpretation risk is the shift definition above.
