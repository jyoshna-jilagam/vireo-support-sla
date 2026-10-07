import csv
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from .data_loader import DATA_DIR
from .sla import TARGET_MINUTES

FMT = "%Y-%m-%d %H:%M"


def data_quality_checks(raw_tickets, agents, df):
    """Return a list of (check, result, detail). result is PASS, WARN or INFO."""
    out = []
    dup_ids = int(raw_tickets["ticket_id"].duplicated().sum())
    out.append(("Duplicate ticket ids in raw file", "INFO", f"{dup_ids} rows removed, helpdesk copy kept"))
    out.append(("Ticket ids unique after cleaning", "PASS" if df["ticket_id"].is_unique else "FAIL", f"{len(df)} tickets"))
    miss = int(df["first_response_at"].isna().sum() + df["created_at"].isna().sum())
    out.append(("Missing created or first response time", "PASS" if miss == 0 else "FAIL", f"{miss} rows"))
    neg = int((df["first_response_at"] < df["created_at"]).sum())
    out.append(("First response before creation", "PASS" if neg == 0 else "FAIL", f"{neg} rows"))
    bad_res = int((df["resolved_at"] < df["first_response_at"]).sum())
    out.append(("Resolution before first response", "PASS" if bad_res == 0 else "FAIL", f"{bad_res} rows"))
    unknown = int((~df["agent_id"].isin(agents["agent_id"])).sum())
    out.append(("Agent id missing from roster", "PASS" if unknown == 0 else "FAIL", f"{unknown} rows"))
    no_roster = int(df["agent_shift"].isna().sum())
    out.append(("Tickets with no roster row valid on creation date", "PASS" if no_roster == 0 else "WARN", f"{no_roster} rows"))
    unknown_ch = int((~df["channel"].isin(TARGET_MINUTES)).sum())
    out.append(("Channel without an SLA target", "PASS" if unknown_ch == 0 else "FAIL", f"{unknown_ch} rows"))
    lo, hi = df["created_at"].min(), df["created_at"].max()
    out.append(("Created date range (UTC)", "INFO", f"{lo:%Y-%m-%d} to {hi:%Y-%m-%d}"))
    ivr = int(df["customer_message"].str.startswith("[IVR transcript]").sum())
    out.append(("IVR transcripts present in message field", "INFO", f"{ivr} tickets, not used by the SLA calculation"))
    return out


def _roster_rows(agents_path):
    with open(agents_path, newline="") as f:
        return list(csv.DictReader(f))


def independent_recompute(row, roster_rows):
    """Plain-python recomputation of one ticket, written separately from the pandas code."""
    created = datetime.strptime(row["created_at"], FMT)
    first = datetime.strptime(row["first_response_at"], FMT)
    minutes = (first - created).total_seconds() / 60
    breach = minutes > TARGET_MINUTES[row["channel"]]
    ist = created + timedelta(hours=5, minutes=30)
    monday = (ist - timedelta(days=ist.weekday())).date()
    h = ist.hour
    shift = "Morning" if 6 <= h < 14 else "Day" if 14 <= h < 22 else "Night"
    agent_shift = None
    for r in roster_rows:
        if r["agent_id"] != row["agent_id"]:
            continue
        start = datetime.strptime(r["from_date"], "%Y-%m-%d").date()
        end = datetime.strptime(r["to_date"], "%Y-%m-%d").date() if r["to_date"] else None
        if start <= ist.date() and (end is None or ist.date() <= end):
            agent_shift = r["shift"]
    return {"breach": breach, "week_start": monday, "creation_shift": shift, "agent_shift": agent_shift}


def audit_sample(df, n=500, seed=42, data_dir=DATA_DIR):
    """Compare tool output with the independent recomputation for a random sample of tickets."""
    roster_rows = _roster_rows(Path(data_dir) / "agents.csv")
    with open(Path(data_dir) / "tickets.csv", newline="") as f:
        raw = {}
        for r in csv.DictReader(f):
            if r["ticket_id"] not in raw or r["source_system"] == "helpdesk":
                raw[r["ticket_id"]] = r
    sample = df.sample(n=min(n, len(df)), random_state=seed)
    rows, errors = [], 0
    for _, t in sample.iterrows():
        exp = independent_recompute(raw[t["ticket_id"]], roster_rows)
        got_agent_shift = None if pd.isna(t["agent_shift"]) else t["agent_shift"]
        checks = {
            "breach": bool(t["breach"]) == exp["breach"],
            "week": t["week_start"].date() == exp["week_start"],
            "creation_shift": t["creation_shift"] == exp["creation_shift"],
            "agent_shift": got_agent_shift == exp["agent_shift"],
        }
        wrong = [k for k, ok in checks.items() if not ok]
        errors += bool(wrong)
        rows.append({"ticket_id": t["ticket_id"], "channel": t["channel"], "response_minutes": t["response_minutes"],
                     "tool_breach": bool(t["breach"]), "expected_breach": exp["breach"],
                     "tool_creation_shift": t["creation_shift"], "expected_creation_shift": exp["creation_shift"],
                     "mismatch": ",".join(wrong)})
    audit = pd.DataFrame(rows)
    summary = {"tested": len(audit), "correct": len(audit) - errors, "incorrect": errors,
               "error_rate": errors / len(audit)}
    return summary, audit


def weekly_reconciliation(df):
    """Weekly counts must add back to the ticket-level totals."""
    wk = df.groupby("week_start")["breach"].agg(["size", "sum"])
    return bool(wk["size"].sum() == len(df) and wk["sum"].sum() == df["breach"].sum())
