# Vireo Audio: First-Response SLA Breach Report

A small tool that shows which agents and shifts breach the first-response SLA, week by week, built from the helpdesk export supplied by Vireo Audio. All numbers come from deterministic Python code. No language model and no API key are used.

## Key result

| Measure | Value |
|---|---|
| Tickets analysed (after removing 616 duplicate rows) | 11,200 |
| Overall breach rate | 21.8% (2,440 breaches) |
| Before 30 Jun 2025 / since | 9.2% / 25.0% |
| Tickets arriving 22:00-06:00 IST, since 30 Jun 2025 | 79.1% breach, 22% of volume, 71% of breaches |
| Tickets arriving 06:00-22:00 IST, since 30 Jun 2025 | 9.4% breach |
| Validation sample | 500 tickets recomputed independently, 0 differences |

Breaches are driven by when a ticket arrives, not by individual agents. See `memo.md` for the business summary and `methodology.md` for the rules used.

## Requirements

- Python 3.10 or newer (developed and tested on Python 3.12)
- Tested with pandas 3.0, streamlit 1.65, plotly 7.1
- Internet access for the one-time `pip install`

## Setup and run

```bash
git clone https://github.com/jyoshna-jilagam/vireo-support-sla.git
cd vireo-support-sla

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_analysis.py             # writes CSV and JSON results to outputs/
python -m pytest -q                # runs the 10 tests
streamlit run app.py               # opens the dashboard at http://localhost:8501
```

## Using the dashboard

- **Overview**: totals, weekly trend, and a plain-text summary generated from the numbers. Filter by week range and channel in the sidebar.
- **Agents**: breaches and breach rate per resolving agent, with a second rate that excludes overnight arrivals. Low-volume rows are flagged.
- **Shifts**: breach rate by arrival shift and by the agent's rostered shift.
- **Ticket evidence**: every breached ticket with creation time, first response, target and minutes taken.
- **Validation**: data-quality checks and the 500-ticket independent recomputation.
- **Methodology**: the rules used.

## Project layout

```
app.py                Streamlit dashboard
run_analysis.py       Builds all output files
src/data_loader.py    Reads CSVs, removes duplicates, converts UTC to IST
src/sla.py            Targets, breach flag, week, shift, credit
src/analysis.py       Summaries, agent table, cost scenario
src/validation.py     Data-quality checks and independent recomputation
tests/test_sla.py     Unit tests
data/                 tickets.csv and agents.csv
outputs/              Generated results
memo.md               One-page memo to the client
methodology.md        Definitions, decisions, scope
submission-form.md    Completed assessment form
recording-script.md   Script for the 3-minute recording
```

## Input files

Only `data/tickets.csv` and `data/agents.csv` are needed and are included. The customers, orders and products files, the support policy PDF and the email thread were supplied by the client and are not republished here. They are not required to run anything: a first-response SLA does not use customers, orders or products. The rules taken from the policy and email are summarised in `methodology.md`.

## Method in brief

- Response time is `first_response_at - created_at`. A breach is a response later than the channel target: chat 15 min, voice 2 h, social 4 h, email 8 h.
- Timestamps are UTC. Shifts and weeks use IST (UTC + 5:30). Weeks start on Monday.
- Duplicate ticket ids (legacy and helpdesk copies) are collapsed to one row.
- Agents are the resolving agent, as the policy specifies. Shifts are shown two ways: when the ticket arrived, and the agent's roster shift on that date.
- Ranking shows ticket counts and 95% Wilson intervals, and flags agents with fewer than 30 tickets.

## Validation

- `run_analysis.py` runs the data-quality checks and a 500-ticket independent recomputation (plain Python, fixed random seed) and saves the results to `outputs/summary.json` and `outputs/audit_sample.csv`.
- Result on the supplied data: 500 tested, 500 matched, 0 differences. With zero differences in 500, the true implementation error rate is likely below about 0.6% (rule of three).
- This checks the code, not the interpretation of the policy.

## Assumptions and limitations

- The export holds the resolving agent, not the agent who sent the first reply. Agent figures are therefore approximate.
- Whether the Night shift was formally disbanded is inferred from the roster (Night rows end 29 Jun 2025) and the breach pattern. It should be confirmed with the client.
- The Rs 350 credit is counted only for resolved or closed breached tickets. The cost of extra overnight cover is not estimated.
- CSAT, refunds, handle time and the orders, customers and products files are out of scope.
- The target in `memo.md` (overnight breach rate from 79% to 40%) is a proposal, not a forecast.
