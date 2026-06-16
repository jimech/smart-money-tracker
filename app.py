"""Smart Money Tracker — Streamlit app.

Run with:  streamlit run app.py

This is the M0 placeholder. Real screens (the screener and company detail
views) arrive in milestone M4.
"""
import streamlit as st

from smart_money import config

st.set_page_config(page_title="Smart Money Tracker", page_icon="📈", layout="wide")

st.title("Smart Money Tracker")
st.caption(
    "Tracking open-market insider buying from SEC filings — "
    "and testing whether it beats the market."
)

if config.user_agent_is_configured():
    st.success("SEC User-Agent configured — you're good to fetch.", icon="✅")
else:
    st.warning(
        'Set your SEC contact email before fetching data. In your terminal:\n\n'
        '`export SEC_USER_AGENT="Your Name your-email@gmail.com"`\n\n'
        "The SEC blocks requests without a real contact.",
        icon="⚠️",
    )

st.subheader("Current signal settings")
c1, c2, c3 = st.columns(3)
c1.metric("Min insiders (cluster)", config.CLUSTER_MIN_INSIDERS)
c2.metric("Window (trading days)", config.CLUSTER_WINDOW_DAYS)
c3.metric("Min combined buy", f"${config.CLUSTER_MIN_USD:,}")

st.subheader("Build status")
st.markdown(
    "- ✅ **M0** — project scaffold (you are here)\n"
    "- ⬜ **M1** — EDGAR client + ticker/CIK resolver\n"
    "- ⬜ **M2** — Form 4 ingestion & parsing\n"
    "- ⬜ **M3** — storage & cluster-buy screening\n"
    "- ⬜ **M4** — dashboard\n"
    "- ⬜ **M5** — backtest the thesis\n"
    "- ⬜ **M6** — polish & deploy"
)

st.info("A research and learning project. Not investment advice.", icon="ℹ️")
