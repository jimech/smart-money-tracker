# Smart Money Tracker

Tracks open-market **insider buying** from SEC EDGAR filings, flags **cluster buys**
(several insiders buying the same stock around the same time), and tests whether that
signal actually beats the market.

> A research and learning project. **Not investment advice.**

## Status

🚧 **M0 — project scaffold.** See [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for the full
ticket list and [`THESIS.md`](THESIS.md) for the research thesis behind it.

## Quickstart

```bash
# 1. Clone and enter
git clone https://github.com/<your-username>/smart-money-tracker.git
cd smart-money-tracker

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Tell the SEC who you are (required — anonymous requests are blocked)
export SEC_USER_AGENT="Your Name your-email@gmail.com"

# 5. Run the app
streamlit run app.py

# 6. Run the tests
pytest
```

## Tech stack

Python · requests · lxml · pandas · SQLite · yfinance · Streamlit · plotly

## Project layout

```
smart_money/        package: config now; ingestion, screening, backtest to come
  config.py         SEC headers, endpoints, and signal parameters
app.py              Streamlit dashboard (placeholder for now)
tests/              pytest suite
data/               local SQLite database lives here (gitignored)
```

## License

MIT — see [`LICENSE`](LICENSE).
