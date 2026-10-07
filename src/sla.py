import pandas as pd

TARGET_MINUTES = {"chat": 15, "voice": 120, "social": 240, "email": 480}
CREDIT_INR = 350


def creation_shift(ts_ist):
    """Shift in which the ticket arrived (IST): Morning 06-14, Day 14-22, Night 22-06."""
    hour = ts_ist.dt.hour
    shift = pd.Series("Night", index=ts_ist.index)
    shift[(hour >= 6) & (hour < 14)] = "Morning"
    shift[(hour >= 14) & (hour < 22)] = "Day"
    return shift


def add_sla_columns(df):
    out = df.copy()
    out["response_minutes"] = (out["first_response_at"] - out["created_at"]).dt.total_seconds() / 60
    out["target_minutes"] = out["channel"].map(TARGET_MINUTES)
    out["breach"] = out["response_minutes"] > out["target_minutes"]
    day = out["created_at_ist"].dt.normalize()
    out["week_start"] = day - pd.to_timedelta(out["created_at_ist"].dt.weekday, unit="D")
    out["creation_shift"] = creation_shift(out["created_at_ist"])
    out["credit_inr"] = (out["breach"] & out["status"].isin(["resolved", "closed"])) * CREDIT_INR
    return out


def attach_roster(df, agents):
    """Add the roster row of the resolving agent that was valid on the ticket creation date (IST)."""
    roster = agents.rename(columns={"shift": "agent_shift", "team": "agent_team"})
    m = df[["ticket_id", "agent_id", "created_at_ist"]].merge(roster, on="agent_id", how="left")
    day = m["created_at_ist"].dt.normalize()
    m = m[(day >= m["from_date"]) & (m["to_date"].isna() | (day <= m["to_date"]))]
    cols = ["ticket_id", "name", "site", "agent_team", "agent_shift", "tier"]
    return df.merge(m[cols], on="ticket_id", how="left")
