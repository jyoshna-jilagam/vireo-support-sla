"""Builds all CSV outputs and the validation report. Run: python run_analysis.py"""
from pathlib import Path
import json
import pandas as pd
from src.analysis import build_dataset, summarize, weekly_table, weekly_by, agent_table, cost_view, headline
from src.data_loader import load_raw
from src.validation import data_quality_checks, audit_sample, weekly_reconciliation

OUT = Path("outputs")


def main():
    OUT.mkdir(exist_ok=True)
    raw, agents = load_raw()
    df = build_dataset()
    weekly_table(df).to_csv(OUT / "weekly_breaches.csv", index=False)
    weekly_by(df, "creation_shift").to_csv(OUT / "weekly_by_creation_shift.csv", index=False)
    weekly_by(df, "agent_shift").to_csv(OUT / "weekly_by_agent_shift.csv", index=False)
    agent_table(df).to_csv(OUT / "agent_breaches.csv", index=False)
    summarize(df, ["period", "creation_shift"]).to_csv(OUT / "shift_by_period.csv", index=False)
    summarize(df, ["period", "agent_shift"]).to_csv(OUT / "agent_shift_by_period.csv", index=False)
    summarize(df, ["period", "channel", "night_arrival"]).to_csv(OUT / "channel_by_period.csv", index=False)
    df[df["breach"]].to_csv(OUT / "breached_tickets.csv", index=False)
    summary, audit = audit_sample(df)
    audit.to_csv(OUT / "audit_sample.csv", index=False)
    checks = data_quality_checks(raw, agents, df)
    report = {"headline": headline(df), "cost": cost_view(df), "audit": summary,
              "weekly_reconciles": weekly_reconciliation(df),
              "data_quality": [list(c) for c in checks]}
    (OUT / "summary.json").write_text(json.dumps(report, indent=2, default=float))
    print(json.dumps(report, indent=2, default=float))


if __name__ == "__main__":
    main()
