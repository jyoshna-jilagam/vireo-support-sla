import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from src.analysis import build_dataset, summarize, weekly_table, weekly_by, agent_table, MIN_TICKETS
from src.data_loader import load_raw
from src.validation import data_quality_checks, audit_sample

st.set_page_config(page_title="Vireo SLA Breach Report", layout="wide")


@st.cache_data
def get_data():
    return build_dataset()


@st.cache_data
def get_validation():
    raw, agents = load_raw()
    df = build_dataset()
    summary, audit = audit_sample(df)
    return data_quality_checks(raw, agents, df), summary, audit


def pct(x):
    return f"{x:.1%}"


df_all = get_data()
st.title("Vireo Audio: First-Response SLA Breach Report")

low, high = df_all["week_start"].min().date(), df_all["week_start"].max().date()
start, end = st.sidebar.date_input("Weeks starting between", value=(low, high), min_value=low, max_value=high)
channels = st.sidebar.multiselect("Channel", sorted(df_all["channel"].unique()), default=sorted(df_all["channel"].unique()))
df = df_all[(df_all["week_start"].dt.date >= start) & (df_all["week_start"].dt.date <= end) & df_all["channel"].isin(channels)]
if df.empty:
    st.warning("No tickets in this selection.")
    st.stop()

tab_over, tab_agent, tab_shift, tab_ticket, tab_val, tab_method = st.tabs(
    ["Overview", "Agents", "Shifts", "Ticket evidence", "Validation", "Methodology"])

with tab_over:
    night = df[df["night_arrival"]]
    rest = df[~df["night_arrival"]]
    c = st.columns(4)
    c[0].metric("Tickets", f"{len(df):,}")
    c[1].metric("Breaches", f"{int(df['breach'].sum()):,}")
    c[2].metric("Breach rate", pct(df["breach"].mean()))
    c[3].metric("Credits issued (Rs)", f"{int(df['credit_inr'].sum()):,}")
    c = st.columns(2)
    if len(night):
        c[0].metric("Arrived 22:00-06:00 IST", pct(night["breach"].mean()), f"{len(night):,} tickets", delta_color="off")
    if len(rest):
        c[1].metric("Arrived 06:00-22:00 IST", pct(rest["breach"].mean()), f"{len(rest):,} tickets", delta_color="off")
    if len(night) and len(rest):
        st.info(
            f"In this selection, {night['breach'].sum() / max(df['breach'].sum(), 1):.0%} of breaches are on tickets that "
            f"arrived overnight ({len(night) / len(df):.0%} of tickets). Tickets that arrived in staffed hours breach at "
            f"{pct(rest['breach'].mean())}. This text is built from the numbers above, not written by a model.")
    wk = weekly_table(df)
    st.plotly_chart(px.line(wk, x="week_start", y="breach_rate", markers=True, title="Weekly breach rate (all tickets)",
                            labels={"week_start": "Week starting (Mon, IST)", "breach_rate": "Breach rate"}), width="stretch")
    st.plotly_chart(px.line(weekly_by(df, "creation_shift"), x="week_start", y="breach_rate", color="creation_shift",
                            title="Weekly breach rate by shift in which the ticket arrived",
                            labels={"week_start": "Week starting", "breach_rate": "Breach rate", "creation_shift": "Arrival shift"}),
                    width="stretch")
    st.dataframe(wk.rename(columns={"week_start": "Week starting"}), width="stretch", hide_index=True)

with tab_agent:
    st.write(f"Breaches are attributed to the resolving agent (policy section 3). Agents with fewer than {MIN_TICKETS} "
             "tickets are flagged and should not be ranked. The second rate excludes overnight arrivals, which the agent "
             "could not have answered inside the target.")
    ag = agent_table(df)
    sort_by = st.radio("Sort by", ["breaches", "breach_rate", "daytime_breach_rate"], horizontal=True)
    show = ag.sort_values(sort_by, ascending=False)
    show = show[["agent_id", "name", "agent_team", "tickets", "breaches", "breach_rate", "night_arrival_share",
                 "daytime_tickets", "daytime_breach_rate", "daytime_ci_low", "daytime_ci_high", "daytime_low_volume", "low_volume"]]
    st.dataframe(show.style.format({"breach_rate": "{:.1%}", "night_arrival_share": "{:.1%}", "daytime_breach_rate": "{:.1%}", "daytime_ci_low": "{:.1%}", "daytime_ci_high": "{:.1%}"}),
                 width="stretch", hide_index=True)

with tab_shift:
    a = summarize(df, "creation_shift")
    b = summarize(df.dropna(subset=["agent_shift"]), "agent_shift")
    st.subheader("By arrival shift (when the ticket was created, IST)")
    st.dataframe(a.style.format({"breach_rate": "{:.1%}", "ci_low": "{:.1%}", "ci_high": "{:.1%}"}), width="stretch", hide_index=True)
    st.subheader("By resolving agent's rostered shift (as the helpdesk reports it)")
    st.dataframe(b.style.format({"breach_rate": "{:.1%}", "ci_low": "{:.1%}", "ci_high": "{:.1%}"}), width="stretch", hide_index=True)
    st.plotly_chart(px.bar(summarize(df, ["creation_shift", "channel"]), x="creation_shift", y="breach_rate", color="channel",
                           barmode="group", title="Breach rate by arrival shift and channel"), width="stretch")
    st.caption("Compare the two tables: the Morning roster shift resolves many tickets that arrived overnight.")

with tab_ticket:
    st.write("Every breach with the numbers behind it.")
    who = st.selectbox("Agent", ["All"] + sorted(df["agent_id"].unique()))
    sub = df[df["breach"]]
    if who != "All":
        sub = sub[sub["agent_id"] == who]
    cols = ["ticket_id", "channel", "created_at", "created_at_ist", "first_response_at", "response_minutes",
            "target_minutes", "creation_shift", "agent_id", "name", "agent_shift", "status", "credit_inr"]
    st.write(f"{len(sub):,} breached tickets")
    st.dataframe(sub[cols].sort_values("created_at", ascending=False).head(1000), width="stretch", hide_index=True)

with tab_val:
    checks, summary, audit = get_validation()
    st.subheader("Data quality checks")
    st.dataframe(pd.DataFrame(checks, columns=["Check", "Result", "Detail"]), width="stretch", hide_index=True)
    st.subheader("Independent recomputation on a random sample")
    c = st.columns(4)
    c[0].metric("Tested", summary["tested"])
    c[1].metric("Correct", summary["correct"])
    c[2].metric("Incorrect", summary["incorrect"])
    c[3].metric("Error rate", pct(summary["error_rate"]))
    st.caption("The check re-reads the raw CSV with plain Python and recomputes breach, week, arrival shift and rostered shift. "
               "It tests the implementation, not the interpretation of the policy. Unit tests: run pytest.")
    st.dataframe(audit.head(50), width="stretch", hide_index=True)

with tab_method:
    st.markdown(Path("methodology.md").read_text())
