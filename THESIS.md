# Smart Money Tracker — Project Thesis

*A tool to watch what corporate insiders and large institutions buy with their own money — and a test of whether it predicts anything.*

---

## 1. The question

When the people with the most information about a company — its own executives and directors, and the large institutional funds that research it full-time — put real money into buying its stock, does that buying predict above-average returns?

Stated as a falsifiable hypothesis:

> **H₁:** Stocks that experience *cluster insider buying* — several insiders making open-market purchases of their own company's stock within a short window — go on to outperform the broad market over the following 30–90 days, by an amount large enough to survive trading costs.
>
> **H₀ (null):** Their subsequent returns are statistically indistinguishable from the market.

The whole project exists to gather the evidence and let the data answer, rather than to assume the answer up front.

## 2. Why this might be true

**The asymmetry of insider buying.** Insiders sell their own stock for many unremarkable reasons — paying taxes, buying a house, diversifying, funding a divorce. They buy on the open market, with their own after-tax cash, for essentially one reason: they think the stock is going up. That asymmetry is why insider *buying* has historically carried more signal than insider *selling*. This project deliberately focuses on purchases.

**It's disclosed, by law, on a known clock.** Insiders (officers, directors, and >10% owners) must report transactions on **Form 4** within **two business days**. Institutional managers above \$100M report their holdings quarterly on **Form 13F**, within **45 days** of quarter-end. Both are public and free. The 13F delay matters — it makes that data more "what are the whales accumulating over time" than a fast trade signal — and the project treats it honestly as such.

**The signal is hiding in plain, ugly sight.** Thousands of Form 4s are filed every week as raw XML buried in a government filing system. Most retail investors never look, and the few who do rarely process it systematically. The edge, if any, is in the plumbing — and that plumbing is exactly what makes this a strong engineering portfolio piece.

**Clustering sharpens it.** A single insider buying a small amount is noise. Several insiders at the same company buying around the same time is a stronger statement of conviction. The project's core signal is therefore the *cluster buy*, not the individual transaction.

## 3. What we're building

Two layers on top of the same data:

1. **A live screener / dashboard** — ingests recent Form 4 filings, isolates open-market purchases, flags cluster buys, and shows them in a sortable view with a per-company detail page (insider buys plotted on the price chart).
2. **A backtest engine** — replays the signal across years of history and measures whether cluster-buy events actually beat the market. This is what turns a data viewer into a piece of research.

The tool *is* the experiment: every cluster buy the dashboard surfaces today becomes a future data point for the thesis.

## 4. Data

| Source | What it gives | Key limitation |
|---|---|---|
| **Form 4** (SEC EDGAR) | Individual insider transactions: who, role, date, transaction code, shares, price | Noisy; many transactions are awards/option exercises, not conviction buys |
| **Form 13F** (SEC EDGAR) | Quarterly institutional holdings | Reported with up to a 45-day delay; positions only, not timing |
| **Daily price data** (e.g. `yfinance`) | Stock and benchmark prices for return calculations | Adjusted-close quirks; occasional gaps |

**The transaction code is the heart of the parsing.** Form 4 Table I codes distinguish what actually happened. `P` = open-market/private **purchase** (the conviction signal we want), `S` = sale, `A` = grant/award, `M` = option exercise, `G` = gift. Filtering to `P` is what separates "an insider bet their own money" from "the company handed them shares." Getting this classification right is the single most important correctness requirement in the codebase.

**Source endpoints (all free, no key):**
- Ticker ↔ CIK: `https://www.sec.gov/files/company_tickers.json`
- Per-company history: `https://data.sec.gov/submissions/CIK{10-digit}.json`
- All filings for a day, by form type: EDGAR daily-index under `/Archives/edgar/daily-index/`
- A filing's documents: `https://www.sec.gov/Archives/edgar/data/{CIK}/{accession-no-dashes}/`

## 5. Methodology — how we test the thesis

This is an **event study**. The discipline of doing it honestly is most of the portfolio value.

**Define the signal precisely.** A *cluster buy* = **≥ N distinct insiders** of the same issuer making open-market purchases (code `P`) within a rolling **W-day window**, with combined value above a floor of **\$X**. (Starting point: N = 3, W = 10 trading days, X = \$100k — all configurable so sensitivity can be tested.)

**Measure forward returns.** From each event, compute the stock's return over the next **30 / 60 / 90 trading days**.

**Compare against a benchmark.** Subtract the return of a market benchmark (SPY) over the *same* window to get an **excess return**. Beating the market is the claim; raw returns alone would just reflect a rising market.

**Respect the clock — no look-ahead.** The signal isn't actionable until the filing is public, so the simulated entry is the **next available close after the Form 4 is filed**, never the transaction date itself. This honesty about the 2-day lag is a deliberate guard against the most common backtesting mistake.

**Account for the obvious confounders.** The write-up will explicitly address: survivorship bias (include delisted names), transaction costs (apply a cost haircut), small-sample and multiple-testing risk (report distribution and a bootstrap/t-test, not just an average), and size effects (small caps move more).

## 6. What would make the thesis right — or wrong

The project commits to a verdict in advance, so it can't be quietly fudged later:

- **Supports H₁:** mean/median excess return is positive, holds across reasonable parameter choices, and stays positive after a cost haircut, with a distribution that isn't driven by one or two outliers.
- **Supports H₀ (refutes the edge):** excess returns cluster around zero, flip sign with small parameter changes, or vanish once costs are applied.

**Either outcome is a successful project.** "We built the tool and the signal didn't hold up after costs" is an honest, valuable, and genuinely impressive result to present — it shows you can kill your own hypothesis with evidence.

## 7. Limitations & honest caveats

- 13F's reporting delay means institutional data lags reality by weeks.
- Form 4 covers transactions, not intent; even a real purchase can be wrong.
- Historical patterns need not persist; a signal that worked can be arbitraged away.
- This is a research and learning project. **Nothing here is investment advice.**

## 8. Why this project (for the portfolio)

It demonstrates four things at once that a typical junior project doesn't:

1. **Wrangling messy real-world regulatory data** (EDGAR XML), not a clean Kaggle CSV.
2. **A full-stack data application** — ingestion, storage, screening, and an interactive dashboard.
3. **Sound quantitative methodology** — an event study with explicit controls for look-ahead and survivorship bias.
4. **Intellectual honesty** — a falsifiable claim, a pre-committed verdict, and a willingness to report a negative result.

The headline for a recruiter or interviewer: *"I built a tool that tracks insider buying from SEC filings, then used it to test whether the signal actually beats the market — and here's exactly what I found and why I trust it."*
