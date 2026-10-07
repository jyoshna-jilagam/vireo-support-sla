# Submission Form: Vireo Audio SLA Breach Report

Candidate: Jyoshna Jilagam (jyoshnajilagam25@gmail.com)

## What did you build, and what business outcome does it move? State the number and the money.
A Streamlit dashboard and a script (`run_analysis.py`) that produce weekly first-response SLA breach reports by agent and by shift, with ticket-level evidence for every breach. The finding that matters: since 30 June 2025, tickets arriving 22:00-06:00 IST breach 79.1% of the time (1,581 of 2,000), against 9.4% for tickets arriving in staffed hours. They are 22% of volume and 71% of breaches. The Morning roster shift looks worst (36.7%) because it answers the overnight queue.

Goal: cut the overnight breach rate from 79% to 40% within eight weeks of changing overnight cover. That takes the overall rate from 25.0% to about 16.2%. At the policy credit of Rs 350 per breach, it saves about Rs 65,000 per quarter in the export (current overnight credits are about Rs 131,500 a quarter; matching the daytime rate would save about Rs 116,000). These figures exclude the cost of the extra cover, which the data does not price.

## What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)?
No paid calls. The tool uses no LLM, no API and no cloud service, so a run costs Rs 0 in usage. One run on the 11,816-row export takes about 2 seconds on a laptop.

A month at 650 tickets a week: 650 x 52 / 12 = about 2,817 tickets. That is about 3.7 times the export's recent weekly volume of 176 (176 x 3.7 = 650). Run time grows roughly in line, so a month is still a few seconds and still Rs 0. Hosting is not included because the tool runs locally.

## How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.
- 500 tickets chosen at random (fixed seed) were recomputed from the raw CSV by separate plain-Python code. Compared: breach flag, week, arrival shift and rostered shift. Result: 500 correct, 0 incorrect, observed error rate 0%. By the rule of three the true rate is likely under about 0.6%.
- 10 unit tests cover: exactly on target (not a breach), one minute over, each channel target, UTC to IST, shift boundaries, Monday week start across midnight IST, duplicate handling, credit rules, interval width, and a real-data sample.
- Data checks found no missing or reversed timestamps and no agents missing from the roster. Weekly counts add back to the ticket totals.
- What it gets wrong: the check shares my reading of the policy, so it would not catch a wrong interpretation. The kind of case most likely wrong is a ticket where the resolving agent is not the person who sent the first reply. The export does not record the first replier, so I cannot measure how often that happens.

## Did you change, narrow, or push back on the client's ask? What, when, and why.
Yes, after the first calculation. Neha asked for breaches by agent and shift and said the Morning team is the bulk of the breaches. That is true as counted, but I split by when the ticket arrived and found the cause is overnight arrivals. So I made arrival shift the primary view, kept the agent view with a volume flag and a rate that excludes overnight arrivals, and advised against acting on individual agents. I also kept the report free of a "wall of red" ranking for the Morning team, following Priya's concern, and framed the recommendation as moving existing capacity because Arjun said headcount is frozen.

## What is wrong with what you are handing us? Be specific.
- Agent figures use the resolving agent. The first replier is not in the data.
- The cause (Night shift ending on 29 June 2025) is inferred from the roster and the timing, not confirmed.
- The 40% target is a proposal I chose, not a forecast or a measured capability.
- The saving ignores the cost of providing overnight cover, so it is not a net figure.
- The export averages about 176 tickets a week, not 650. If it is a sample, the rupee figures are understated by up to about 3.7 times. I did not scale them.
- The first and last weeks are partial (data starts on 1 Jan 2025 and ends on 30 Jun 2026), so their weekly rates are noisier.
- 120 breached tickets are still open or pending, so they count as breaches but not yet as credits.
- The dashboard shows at most 1,000 breached tickets in the evidence table. The full list is in `outputs/breached_tickets.csv`.
- The app was smoke-tested but has no automated UI tests. Tested on Python 3.12 only.

## What did you deliberately leave out, and why that rather than something else?
- Agent-level performance ranking for action: a ranking would mostly rank who works the overnight queue, and it would hurt morale.
- CSAT, refunds, handle time and the orders, customers and products files: none changes a first-response breach.
- A cost model for overnight cover: the data has no hours or rota to price it.
- An LLM summary: SLA arithmetic must be deterministic, and a template on computed numbers says the same thing without a model.

## Anything you built or found that nobody asked for?
- Duplicates: 616 tickets appear twice (migration re-import) and were collapsed.
- The overnight pattern above, including that every overnight breach was answered between 06:00 and 10:00 IST.
- A check on the credit disagreement: in the export, monthly credits rose from about Rs 11,500 (Jan-Jun 2025) to about Rs 62,000 (Jul 2025-Jun 2026), a rise of about 5.4 times. That supports Arjun's view that the credit line rose sharply and does not support Priya's view that it is flat. It is for Finance to reconcile with the P&L.
- A volume mismatch between the export and the quoted 650 tickets a week.

## What did you use AI for?
Claude (Anthropic, Sonnet family) through the chat interface. It helped read the files and spot the traps (UTC against IST, duplicates, resolver against first responder), propose the plan, write the code, tests and documents, and run the checks. Where it wasted time: the early plan was larger than needed (more files and an LLM feature) and I cut it back. Thrown away: the LLM summary, a cost-of-cover estimate and the CSAT analysis. No AI runs inside the tool. API cost: none.
Screen recording: https://drive.google.com/file/d/1spJLjY6ydyc02ZtbTdlJ_4EoO1kb3FQo/view?usp=sharing

## Your Public Google Drive Link
https://drive.google.com/file/d/1spJLjY6ydyc02ZtbTdlJ_4EoO1kb3FQo/view?usp=sharing

## Someone picks this up on Monday and you are unreachable. The three things they need to know.
1. Run `python run_analysis.py` and `streamlit run app.py`; all rules are in `methodology.md` and every number comes from `outputs/summary.json`.
2. The headline is overnight arrivals (22:00-06:00 IST) since 30 June 2025. Confirm with Sameer who covered nights after June 2025 before acting.
3. Check whether the export is a sample of the 650 tickets a week before quoting rupee figures, and do not rank individual agents from this report.

## Honest hours spent
HOURS_SPENT

## Github Repo Link
https://github.com/jyoshna-jilagam/vireo-support-sla
