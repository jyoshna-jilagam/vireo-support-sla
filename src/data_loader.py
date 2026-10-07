from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)


def load_raw(data_dir=DATA_DIR):
    tickets = pd.read_csv(
        Path(data_dir) / "tickets.csv",
        parse_dates=["created_at", "first_response_at", "resolved_at"],
    )
    agents = pd.read_csv(Path(data_dir) / "agents.csv", parse_dates=["from_date", "to_date"])
    return tickets, agents


def clean_tickets(tickets):
    """Drop migration duplicates (keep the helpdesk copy) and add IST timestamps."""
    df = tickets.copy()
    df["_pref"] = (df["source_system"] != "helpdesk").astype(int)
    df = df.sort_values(["ticket_id", "_pref"]).drop_duplicates("ticket_id").drop(columns="_pref")
    for col in ["created_at", "first_response_at", "resolved_at"]:
        df[col + "_ist"] = df[col] + IST_OFFSET
    return df.reset_index(drop=True)
