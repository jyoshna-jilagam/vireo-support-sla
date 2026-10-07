import math
import pandas as pd
from .data_loader import load_raw, clean_tickets
from .sla import add_sla_columns, attach_roster

NIGHT_SHIFT_ENDED = pd.Timestamp("2025-06-30")
MIN_TICKETS = 30


def build_dataset(data_dir=None):
    tickets, agents = load_raw(data_dir) if data_dir else load_raw()
    df = add_sla_columns(clean_tickets(tickets))
    df = attach_roster(df, agents)
    df["night_arrival"] = df["creation_shift"] == "Night"
    df["period"] = (df["created_at_ist"] < NIGHT_SHIFT_ENDED).map(
        {True: "Before 30 Jun 2025", False: "From 30 Jun 2025"}
    )
    return df


def wilson(breaches, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = breaches / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    denom = 1 + z * z / n
    return (centre - margin) / denom, (centre + margin) / denom


def summarize(df, by):
    g = df.groupby(by).agg(tickets=("breach", "size"), breaches=("breach", "sum")).reset_index()
    g["breach_rate"] = g["breaches"] / g["tickets"]
    bounds = [wilson(b, n) for b, n in zip(g["breaches"], g["tickets"])]
    g["ci_low"] = [b[0] for b in bounds]
    g["ci_high"] = [b[1] for b in bounds]
    g["low_volume"] = g["tickets"] < MIN_TICKETS
    return g


def weekly_table(df):
    return summarize(df, "week_start")


def weekly_by(df, col):
    return summarize(df, ["week_start", col])


def agent_table(df):
    """Per resolving agent: overall rate plus rate on tickets that arrived in staffed hours."""
    overall = summarize(df, ["agent_id", "name"]).drop(columns=["ci_low", "ci_high"])
    night_share = df.groupby("agent_id")["night_arrival"].mean().rename("night_arrival_share")
    day_part = summarize(df[~df["night_arrival"]], "agent_id")[["agent_id", "tickets", "breaches", "breach_rate", "ci_low", "ci_high"]]
    day_part.columns = ["agent_id", "daytime_tickets", "daytime_breaches", "daytime_breach_rate", "daytime_ci_low", "daytime_ci_high"]
    out = overall.merge(night_share, on="agent_id").merge(day_part, on="agent_id", how="left")
    meta = df.drop_duplicates("agent_id").set_index("agent_id")[["agent_team"]]
    out = out.merge(meta, on="agent_id", how="left")
    out["daytime_low_volume"] = out["daytime_tickets"].fillna(0) < MIN_TICKETS
    return out.sort_values("breaches", ascending=False).reset_index(drop=True)


def cost_view(df):
    post = df[df["period"] == "From 30 Jun 2025"]
    night = post[post["night_arrival"]]
    day = post[~post["night_arrival"]]
    quarters = (post["created_at_ist"].max() - post["created_at_ist"].min()).days / 91.25
    night_credit = night["credit_inr"].sum()
    # Credits that would remain if night arrivals breached at the daytime rate
    day_rate = day["breach"].mean()
    resolved_night = night["status"].isin(["resolved", "closed"]).sum()
    floor_credit = resolved_night * day_rate * 350
    target_night_rate = 0.40
    night_rate = night["breach"].mean()
    night_share = len(night) / len(post)
    target_credit = night_credit * target_night_rate / night_rate
    return {
        "target_night_rate": target_night_rate,
        "target_overall_rate": (1 - night_share) * day_rate + night_share * target_night_rate,
        "target_saving_per_quarter": (night_credit - target_credit) / quarters,
        "quarters_in_period": quarters,
        "night_credit_total": night_credit,
        "night_credit_per_quarter": night_credit / quarters,
        "recoverable_per_quarter": (night_credit - floor_credit) / quarters,
        "daytime_breach_rate": day_rate,
    }


def headline(df):
    post = df[df["period"] == "From 30 Jun 2025"]
    pre = df[df["period"] == "Before 30 Jun 2025"]
    return {
        "tickets": len(df),
        "breaches": int(df["breach"].sum()),
        "overall_rate": df["breach"].mean(),
        "pre_rate": pre["breach"].mean(),
        "post_rate": post["breach"].mean(),
        "post_night_rate": post[post["night_arrival"]]["breach"].mean(),
        "post_day_rate": post[~post["night_arrival"]]["breach"].mean(),
        "post_night_share_of_breaches": post[post["night_arrival"]]["breach"].sum() / post["breach"].sum(),
        "post_night_share_of_tickets": post["night_arrival"].mean(),
        "last_8_week_rate": df[df["week_start"] >= df["week_start"].max() - pd.Timedelta(weeks=8)]["breach"].mean(),
    }
