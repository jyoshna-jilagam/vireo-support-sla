import pandas as pd
from src.sla import add_sla_columns, creation_shift
from src.data_loader import clean_tickets, IST_OFFSET
from src.analysis import wilson, build_dataset
from src.validation import audit_sample


def make(created, first, channel="chat", status="resolved", source="helpdesk", tid="T1"):
    df = pd.DataFrame([{
        "ticket_id": tid, "created_at": pd.Timestamp(created), "first_response_at": pd.Timestamp(first),
        "resolved_at": pd.Timestamp(first) + pd.Timedelta(hours=1), "channel": channel,
        "status": status, "source_system": source}])
    return add_sla_columns(clean_tickets(df))


def test_exactly_on_target_is_not_a_breach():
    assert not make("2026-01-05 10:00", "2026-01-05 10:15").loc[0, "breach"]


def test_one_minute_over_is_a_breach():
    assert make("2026-01-05 10:00", "2026-01-05 10:16").loc[0, "breach"]


def test_targets_per_channel():
    assert not make("2026-01-05 10:00", "2026-01-05 12:00", "voice").loc[0, "breach"]
    assert make("2026-01-05 10:00", "2026-01-05 14:01", "social").loc[0, "breach"]
    assert not make("2026-01-05 10:00", "2026-01-05 18:00", "email").loc[0, "breach"]


def test_utc_to_ist_conversion_and_shift():
    row = make("2026-01-05 16:30", "2026-01-05 16:40")  # 22:00 IST, Night starts
    assert row.loc[0, "created_at_ist"] == pd.Timestamp("2026-01-05 22:00")
    assert row.loc[0, "creation_shift"] == "Night"


def test_shift_boundaries():
    ts = pd.Series(pd.to_datetime(["2026-01-05 05:59", "2026-01-05 06:00", "2026-01-05 13:59",
                                   "2026-01-05 14:00", "2026-01-05 21:59", "2026-01-05 22:00"]))
    assert creation_shift(ts).tolist() == ["Night", "Morning", "Morning", "Day", "Day", "Night"]


def test_week_starts_monday_in_ist():
    # Sunday 18:31 UTC is Monday 00:01 IST, so it belongs to the next week
    row = make("2026-01-04 18:31", "2026-01-04 18:40")
    assert row.loc[0, "week_start"] == pd.Timestamp("2026-01-05")


def test_duplicate_ticket_keeps_helpdesk_row():
    a = make("2025-02-01 10:00", "2025-02-01 10:05", source="legacy_fd")
    b = make("2025-02-01 10:00", "2025-02-01 10:05", source="helpdesk")
    raw = pd.concat([a, b])[["ticket_id", "created_at", "first_response_at", "resolved_at", "channel", "status", "source_system"]]
    out = clean_tickets(raw)
    assert len(out) == 1 and out.loc[0, "source_system"] == "helpdesk"


def test_credit_only_on_resolved_or_closed_breaches():
    assert make("2026-01-05 10:00", "2026-01-05 11:00").loc[0, "credit_inr"] == 350
    assert make("2026-01-05 10:00", "2026-01-05 11:00", status="open").loc[0, "credit_inr"] == 0


def test_wilson_interval_widens_for_small_samples():
    lo_small, hi_small = wilson(5, 10)
    lo_big, hi_big = wilson(500, 1000)
    assert (hi_small - lo_small) > (hi_big - lo_big)


def test_real_data_audit_sample_has_no_mismatch():
    df = build_dataset()
    summary, _ = audit_sample(df, n=200, seed=1)
    assert summary["incorrect"] == 0
    assert df["ticket_id"].is_unique
