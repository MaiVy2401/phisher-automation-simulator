"""
PhishER Automation Confidence Simulator ("what-if" simulator)
-------------------------------------------------------------
Problem: PhishER + PhishML can already auto-handle user-reported emails, but only
above confidence thresholds the admin picks. Admins don't know what number is
safe, so many keep reviewing everything by hand -> "PhishER takes too much time."

Idea: replay the admin's OWN past reported emails (ML label + confidence + the
admin's final decision) under any threshold setting, and show:
  - how much work would have been automated (time saved)
  - exactly which mistakes would have happened (risk)
Then recommend the setting with the most automation for a chosen risk appetite,
and explain it in plain English (Claude, optional).

Run:  streamlit run app.py
"""

import itertools
import os

import pandas as pd
import streamlit as st

LABELS = ["Clean", "Spam", "Threat"]
GRID = [round(x, 2) for x in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.97, 0.99, 1.01]]  # 1.01 = "never automate"


# ---------------------------------------------------------------------------
# 1) Core simulation: replay history under a threshold setting
# ---------------------------------------------------------------------------
def mistake_type(pred: str, truth: str) -> str:
    """Not all mistakes are equal. This severity scale is a PRODUCT decision."""
    if pred == truth:
        return "Correct"
    if truth == "Threat":
        return "🚨 Threat let through"          # worst: a real phish goes back to the inbox
    if pred == "Threat":
        return "⚠️ Real email removed"           # false positive: the #1 customer complaint
    return "Minor (clean/spam mix-up)"


def simulate(df: pd.DataFrame, t: dict) -> pd.DataFrame:
    out = df.copy()
    out["threshold"] = out["ml_label"].map(t)
    out["automated"] = out["ml_confidence"] >= out["threshold"]
    out["outcome"] = [mistake_type(p, a) if auto else "Human review"
                      for p, a, auto in zip(out["ml_label"], out["admin_final_label"], out["automated"])]
    return out


def summarize(sim: pd.DataFrame, minutes_per_review: float, months: float, hourly_cost: float = 0.0) -> dict:
    n = len(sim)
    auto = sim["automated"].sum()
    hours = auto * minutes_per_review / 60 / months
    return {
        "automation_rate": auto / n if n else 0,
        "hours_saved_per_month": hours,
        "dollars_saved_per_month": hours * hourly_cost,
        "threats_let_through": int((sim["outcome"] == "🚨 Threat let through").sum()),
        "real_emails_removed": int((sim["outcome"] == "⚠️ Real email removed").sum()),
        "minor": int((sim["outcome"] == "Minor (clean/spam mix-up)").sum()),
        "to_review": int((~sim["automated"]).sum()),
    }


RISK_PROFILES = {
    "Cautious": {"threats": 0, "fp_rate": 0.005, "desc": "Zero threats let through, almost no real emails removed."},
    "Balanced": {"threats": 0, "fp_rate": 0.02, "desc": "Zero threats let through, a few real emails removed (users can ask for them back)."},
    "Aggressive": {"threats": 1, "fp_rate": 0.05, "desc": "Maximum time saved; accepts rare mistakes."},
}


def recommend(df: pd.DataFrame, profile: dict, minutes: float, months: float, hourly_cost: float = 0.0):
    """Grid search: the setting with the MOST automation that stays inside the risk budget."""
    best = None
    for tc, ts, tt in itertools.product(GRID, GRID, GRID):
        s = summarize(simulate(df, {"Clean": tc, "Spam": ts, "Threat": tt}), minutes, months, hourly_cost)
        if s["threats_let_through"] > profile["threats"]:
            continue
        if s["real_emails_removed"] / len(df) > profile["fp_rate"]:
            continue
        if best is None or s["automation_rate"] > best[1]["automation_rate"]:
            best = ({"Clean": tc, "Spam": ts, "Threat": tt}, s)
    return best


def fmt_t(x: float) -> str:
    return "never" if x > 1 else f"{x:.0%}"


def fmt_usd(x: float) -> str:
    return f"${x:,.0f}"


def explain_offline(t: dict, s: dict, profile_name: str, hourly_cost: float) -> str:
    return (
        f"**Recommended ({profile_name})**: auto-handle Clean at ≥{fmt_t(t['Clean'])}, "
        f"Spam at ≥{fmt_t(t['Spam'])}, Threat at ≥{fmt_t(t['Threat'])} confidence.\n\n"
        f"On your last month of reports this would have handled **{s['automation_rate']:.0%}** automatically, "
        f"saving about **{s['hours_saved_per_month']:.1f} admin hours/month** "
        f"(**≈ {fmt_usd(s['dollars_saved_per_month'])}/month** at {fmt_usd(hourly_cost)}/hour). "
        f"Threats let through: **{s['threats_let_through']}**. Real emails wrongly removed: **{s['real_emails_removed']}**. "
        f"You would still review **{s['to_review']}** emails by hand: the ones the model is unsure about."
    )


def explain_with_claude(t, s, profile_name, api_key, model) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "You are helping a busy IT admin at a small company decide whether to turn on automation "
        "for user-reported phishing emails. Explain this recommendation in under 120 words, plain English, "
        "no jargon, honest about the risks, and end with one sentence they could send their boss.\n\n"
        f"Risk appetite: {profile_name}\nThresholds (min confidence to auto-handle): {t}\n"
        f"Results replayed on last month's reports: {s}\n"
        "Only use the numbers given. Do not invent statistics."
    )
    msg = client.messages.create(model=model, max_tokens=300, temperature=0,
                                 messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text


# ---------------------------------------------------------------------------
# 2) UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PhishER Automation Simulator", page_icon="🎚️", layout="wide")
st.title("🎚️ PhishER Automation Confidence Simulator")
st.caption("A “what-if” test track: replay your own past reported emails under any automation setting "
           "before you turn it on. Prototype · synthetic data for a fictional company (Acme Dental).")

with st.sidebar:
    st.header("Your data")
    up = st.file_uploader("Upload reported-email history (CSV)", type="csv",
                          help="Columns: subject, sender, ml_label, ml_confidence, admin_final_label")
    df = pd.read_csv(up) if up else pd.read_csv(
        os.path.join(os.path.dirname(__file__), "reported_history.csv"))
    months = st.number_input("Months of history in this file", 0.5, 24.0, 1.0, 0.5)
    minutes = st.slider("Minutes an admin spends per manual review", 1, 15, 3,
                        help="Assumption: validate with real time-on-task data.")
    hourly_cost = st.number_input("Admin hourly cost ($)", min_value=0.0, value=45.0, step=5.0,
                                  help="Fully loaded cost of one admin hour (salary + overhead). Used for $ saved.")
    st.divider()
    st.header("Optional: Claude explanations")
    default_key = os.getenv("ANTHROPIC_API_KEY", "")
    try:
        default_key = default_key or st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    api_key = st.text_input("Anthropic API key", value=default_key, type="password")
    model = st.text_input("Model", value="claude-haiku-5-5")

st.info(f"Loaded **{len(df)} reported emails** · ML was right on "
        f"**{(df['ml_label'] == df['admin_final_label']).mean():.0%}** of them · "
        f"**{(df['admin_final_label'] == 'Threat').mean():.0%}** were real threats.")

tab_sim, tab_curve, tab_rec, tab_about = st.tabs(
    ["🎚️ What-if simulator", "📈 Trade-off curve", "✨ Recommend a setting", "ℹ️ How it works"])

# ---- Tab 1: simulator -------------------------------------------------------
with tab_sim:
    st.write("**Auto-handle a reported email when the ML is at least this confident:**")
    c1, c2, c3 = st.columns(3)
    tc = c1.slider("Clean → release to inbox", 0.50, 1.00, 0.95, 0.01)
    ts = c2.slider("Spam → archive", 0.50, 1.00, 0.90, 0.01)
    tt = c3.slider("Threat → quarantine (PhishRIP)", 0.50, 1.00, 0.80, 0.01)
    sim = simulate(df, {"Clean": tc, "Spam": ts, "Threat": tt})
    s = summarize(sim, minutes, months, hourly_cost)

    m1, m2, m2b, m3, m4, m5 = st.columns(6)
    m1.metric("Automated", f"{s['automation_rate']:.0%}")
    m2.metric("Admin hours saved / month", f"{s['hours_saved_per_month']:.1f}")
    m2b.metric("Admin cost saved / month", fmt_usd(s["dollars_saved_per_month"]),
               help=f"Hours saved × {fmt_usd(hourly_cost)}/hour (sidebar).")
    m3.metric("Still to review by hand", s["to_review"])
    m4.metric("🚨 Threats let through", s["threats_let_through"],
              help="Real threats the automation would have released. Should be 0.")
    m5.metric("⚠️ Real emails removed", s["real_emails_removed"],
              help="Legit emails auto-quarantined as threats (false positives).")
    if s["threats_let_through"]:
        st.error("This setting would have released real threats. Raise the **Clean** and **Spam** thresholds.")
    elif s["automation_rate"] < 0.3:
        st.warning("Safe, but you're still reviewing most emails by hand. Try lowering a threshold.")
    else:
        st.success("No threats let through on your history at this setting.")

    st.write("**What would have happened, by ML label**")
    st.dataframe(pd.crosstab(sim["ml_label"], sim["outcome"]), width="content")

    mistakes = sim[sim["outcome"].isin(["🚨 Threat let through", "⚠️ Real email removed", "Minor (clean/spam mix-up)"])]
    st.write(f"**The {len(mistakes)} automated mistakes, one by one** (this is what builds trust: no black box)")
    st.dataframe(mistakes[["reported_date", "sender", "subject", "ml_label", "ml_confidence",
                           "admin_final_label", "outcome"]].sort_values("outcome"),
                 width="stretch", hide_index=True)

# ---- Tab 2: curve -----------------------------------------------------------
with tab_curve:
    st.write("One threshold for all labels, from relaxed to strict. **Every point is a trade-off: "
             "more time saved always means more risk.** The product decision is where to sit on this curve.")
    rows = []
    for x in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99]:
        r = summarize(simulate(df, {l: x for l in LABELS}), minutes, months)
        rows.append({"threshold": x, "% automated": r["automation_rate"] * 100,
                     "threats let through": r["threats_let_through"],
                     "real emails removed": r["real_emails_removed"]})
    curve = pd.DataFrame(rows).set_index("threshold")
    st.line_chart(curve[["% automated"]])
    st.line_chart(curve[["threats let through", "real emails removed"]])
    st.dataframe(curve, width="content")

# ---- Tab 3: recommend -------------------------------------------------------
with tab_rec:
    profile_name = st.radio("How much risk is your organization comfortable with?",
                            list(RISK_PROFILES), index=1, horizontal=True)
    profile = RISK_PROFILES[profile_name]
    st.caption(profile["desc"])
    if st.button("Find my best setting", type="primary"):
        with st.spinner("Replaying your history under 1,331 settings..."):
            best = recommend(df, profile, minutes, months, hourly_cost)
        if best is None:
            st.error("No setting meets this risk budget on your data. Keep reviewing manually or relax the budget.")
        else:
            t, s = best
            st.session_state["rec"] = (t, s, profile_name)
    if "rec" in st.session_state:
        t, s, pname = st.session_state["rec"]
        # Re-price with the current sidebar rate so $ never goes stale next to the shown rate.
        s = {**s, "dollars_saved_per_month": s["hours_saved_per_month"] * hourly_cost}
        st.markdown(explain_offline(t, s, pname, hourly_cost))
        if api_key:
            if st.button("✨ Explain this for me and my boss (Claude)"):
                try:
                    st.success(explain_with_claude(t, s, pname, api_key, model))
                except Exception as e:
                    st.warning(f"Claude call failed ({type(e).__name__}); the summary above still stands.")
        else:
            st.caption("Add an API key in the sidebar to get a plain-English explanation from Claude.")

# ---- Tab 4: about -----------------------------------------------------------
with tab_about:
    st.markdown("""
**The problem.** PhishER and PhishML can already auto-handle reported emails, but only above confidence
thresholds the admin chooses. Picking a number feels risky, so many admins leave automation off and review
everything by hand. Customers then say *"PhishER takes too much time."* The feature exists; the **trust** doesn't.

**What this does.** Replays the admin's *own* past reported emails (ML label + confidence + the admin's final
decision) under any setting, and shows time saved vs. the exact mistakes that would have happened.

**Design choices**
- Mistakes are ranked by severity: a threat let through ≫ a real email removed ≫ a clean/spam mix-up.
- Separate thresholds per label, because the cost of being wrong differs by label.
- Recommendation = the most automation that fits the chosen risk budget (constraint-based, not a black box).
- Every automated mistake is listed, so admins can judge for themselves.
- Claude only *explains* numbers the simulator computed; it is told not to invent statistics.

**Limits.** Past performance ≠ future (attackers change). Re-run monthly. Data here is synthetic.
""")
