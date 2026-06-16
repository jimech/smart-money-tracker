# Smart Money Tracker — Build Plan

Milestones and tickets for building the project described in `THESIS.md`. Each ticket is written to drop straight into GitHub Issues: the `### SM-0X — Title` line is the issue title, everything under it is the body.

---

## Scope

**MVP (shippable portfolio piece):** Milestones M0–M4 — a working, live dashboard that ingests Form 4 filings, flags cluster insider buys, and shows them on price charts.

**The differentiator:** M5 — the backtest that tests whether the signal actually beats the market. This is what elevates the project from "a dashboard" to "research." Ship the MVP first, then make M5 the headline.

**Presentable:** M6 — tests, deployment, and documentation so anyone can run it and you can link it.

## Tech stack

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Default for finance data work |
| HTTP | `requests` | Simple; one shared client enforces SEC headers + rate limit |
| XML parsing | `lxml` | Fast, robust for Form 4 XML |
| Storage | SQLite (`sqlite3` + optionally `SQLAlchemy`) | Zero-setup, file-based, perfect for this scale |
| Data wrangling | `pandas` | Returns math and screening |
| Prices | `yfinance` | Free daily stock + benchmark prices |
| Dashboard | `Streamlit` | Pure-Python UI; fastest path from data to interactive app |
| Charts | Streamlit native + `plotly` | Interactive price overlays |
| Scheduling | GitHub Actions (cron) | Free daily refresh, no server to run |
| Deploy | Streamlit Community Cloud | Free public hosting for the live app |
| Testing | `pytest` | Lock in parser + backtest correctness |

## Architecture (data flow)

```
EDGAR daily-index ──▶ discover Form 4 accession numbers
        │
        ▼
fetch + parse Form 4 XML ──▶ transactions (filter to code P)
        │
        ▼
SQLite  ◀── ticker↔CIK resolver (company_tickers.json)
        │
        ├──▶ screener queries (cluster-buy detection) ──▶ Streamlit dashboard
        │                                                   └─ company detail (yfinance price + buy markers)
        └──▶ backtest engine (forward returns vs SPY) ──▶ results + thesis verdict
```

## Milestones

| # | Milestone | Outcome | Tickets |
|---|---|---|---|
| M0 | Project setup | Repo runs, placeholder app loads | SM-01, SM-02 |
| M1 | EDGAR client + identity | Compliant fetching, ticker↔CIK | SM-03, SM-04 |
| M2 | Form 4 ingestion | Parsed insider transactions | SM-05, SM-06, SM-07 |
| M3 | Storage & screening | Cluster buys detectable in DB | SM-08, SM-09, SM-10 |
| M4 | Dashboard | Live screener + company view | SM-11, SM-12, SM-13 |
| M5 | Backtest | Thesis tested with evidence | SM-14, SM-15, SM-16 |
| M6 | Polish & ship | Tested, deployed, documented | SM-17, SM-18 |

Effort key: **S** ≈ a few hours · **M** ≈ a day or two · **L** ≈ several days.

---

## Tickets

### M0 — Project setup

#### SM-01 — Repo scaffold & environment
**What/why:** Create the skeleton so everything else has a home.
- Git repo, virtual environment, `requirements.txt`, `src/smart_money/` package layout, `.gitignore` (ignore `*.db`, `data/`, `.venv/`), `README.md` stub, `LICENSE`.
- A placeholder `app.py` that launches Streamlit.

**Acceptance criteria:**
- [ ] Fresh clone → `pip install -r requirements.txt` succeeds
- [ ] `streamlit run app.py` opens a placeholder page
- [ ] `data/` and `*.db` are gitignored

**Effort:** S · **Depends on:** —

#### SM-02 — Central config
**What/why:** One place for the values everything else needs, so SEC compliance can't be forgotten.
- `config.py` holding `SEC_USER_AGENT` (your name + contact email — **not** an example.com address), base URLs, and the rate-limit constant (10 req/s).

**Acceptance criteria:**
- [ ] Config is importable across the package
- [ ] `SEC_USER_AGENT` is set to a real contact string

**Effort:** S · **Depends on:** SM-01

### M1 — EDGAR client + identity

#### SM-03 — Compliant EDGAR HTTP client
**What/why:** Every SEC request must carry the required header and stay under the rate limit; centralizing this makes that automatic.
- A `client.get(url)` wrapper around `requests` that always sets the `User-Agent` header, throttles to ≤10 requests/second (token bucket or simple spacing), and retries on 429/5xx with exponential backoff.

**Acceptance criteria:**
- [ ] A request to `data.sec.gov` returns 200 with the header set
- [ ] Sustained calls never exceed 10/sec (verified by a quick test)
- [ ] Transient 429/5xx are retried, then surfaced if they persist

**Effort:** M · **Depends on:** SM-02

#### SM-04 — Ticker ↔ CIK resolver
**What/why:** Filings are keyed by CIK; humans think in tickers.
- Download `company_tickers.json`, build a bidirectional lookup, cache to disk, refresh weekly. Include a helper to zero-pad CIKs to 10 digits.

**Acceptance criteria:**
- [ ] `cik_for("AAPL")` returns `320193`; padded form `0000320193` available
- [ ] `ticker_for(320193)` returns `AAPL`
- [ ] Lookup is cached locally and survives restarts

**Effort:** S · **Depends on:** SM-03

### M2 — Form 4 ingestion

#### SM-05 — Discover recent Form 4 filings
**What/why:** Get the day's universe of insider filings to process.
- Use the EDGAR daily-index for a given date (or range) to list every Form 4, returning CIK, accession number, filing date, and primary-document path.

**Acceptance criteria:**
- [ ] Given a date, returns that day's list of Form 4 accession numbers
- [ ] Handles weekends/holidays (no filings) without erroring

**Effort:** M · **Depends on:** SM-04

#### SM-06 — Fetch & parse Form 4 XML → transactions ⭐ *core ticket*
**What/why:** Turn raw filings into structured transactions. This is the hardest and most important ticket.
- Download a filing's XML and parse Table I (non-derivative) transactions: issuer, owner name, owner role (officer/director/10% owner), transaction date, **transaction code**, shares, price per share, acquired/disposed flag. Compute dollar value (shares × price).
- Handle footnoted/ranged prices and missing fields gracefully.

**Acceptance criteria:**
- [ ] Parses 3 saved real filings correctly, including one buy (code `P`) and one sale (code `S`)
- [ ] Unit-tested against saved XML fixtures (no network in tests)
- [ ] Malformed/empty filings are skipped with a logged reason

**Effort:** L · **Depends on:** SM-05

#### SM-07 — Normalize & classify transactions
**What/why:** Reduce noise to the conviction signal.
- Tag `is_open_market_purchase = (code == "P" and acquired)`. Resolve issuer CIK → ticker. Emit a clean transaction dataclass.

**Acceptance criteria:**
- [ ] Open-market purchases are correctly flagged; awards/exercises are not
- [ ] Each transaction carries its resolved ticker (or is flagged if unmappable)

**Effort:** M · **Depends on:** SM-06

### M3 — Storage & screening

#### SM-08 — SQLite schema & persistence
**What/why:** Durable, queryable storage with no duplicates.
- Tables: `companies`, `filings`, `insider_transactions`. Unique constraint on (accession number + transaction line) so re-ingesting a day is idempotent. Upsert logic.

**Acceptance criteria:**
- [ ] Re-running ingestion for the same date adds zero duplicate rows
- [ ] Basic queries (recent purchases by ticker) return correct results

**Effort:** M · **Depends on:** SM-07

#### SM-09 — Daily ingestion job (CLI)
**What/why:** One command to pull, parse, and store.
- `python -m smart_money.ingest --date YYYY-MM-DD` (default: yesterday). Logs counts of filings seen, parsed, and stored.

**Acceptance criteria:**
- [ ] Running the command populates the DB for that date
- [ ] Safe to run repeatedly (idempotent via SM-08)

**Effort:** M · **Depends on:** SM-08

#### SM-10 — Screener & cluster-buy detection
**What/why:** The core signal logic.
- Query functions with filters (min \$ value, role, date range) plus cluster detection: ≥ N distinct insiders buying (code `P`) in one issuer within a W-day window. Parameters N, W, X configurable.

**Acceptance criteria:**
- [ ] Unit test on synthetic data proves correct cluster detection at boundary cases
- [ ] Returns results ranked by cluster size / total \$

**Effort:** M · **Depends on:** SM-08

### M4 — Dashboard

#### SM-11 — Screener page
**What/why:** The main view of the live tool.
- Streamlit page: sortable table of recent buys with sidebar filters wired to SM-10. Columns: issuer, ticker, # insiders, total \$, cluster flag.

**Acceptance criteria:**
- [ ] Adjusting filters updates the table live
- [ ] Cluster buys are visually highlighted

**Effort:** M · **Depends on:** SM-10

#### SM-12 — Company detail page
**What/why:** See the signal against price — the visual payoff.
- Select a ticker → fetch prices via `yfinance` → plot the price line with insider-buy markers overlaid (marker size ∝ \$ value), plus a table of that company's filings.

**Acceptance criteria:**
- [ ] Selecting a clustered company shows its buys positioned on the price chart
- [ ] Page handles tickers with no price data without crashing

**Effort:** M · **Depends on:** SM-11

#### SM-13 — Caching & UX polish
**What/why:** Make it fast and unbreakable on empty data.
- `st.cache_data` for price fetches and queries; loading and empty states; a short "what am I looking at" blurb on each page.

**Acceptance criteria:**
- [ ] Repeated views don't re-fetch prices unnecessarily
- [ ] Empty results render a friendly message, not an error

**Effort:** S · **Depends on:** SM-12

### M5 — Backtest (test the thesis)

#### SM-14 — Historical event dataset
**What/why:** You can't test a signal without history.
- Backfill cluster-buy events over a chosen window (start with 2–3 years) by ingesting historical daily indexes. Produce an `events` table: issuer, signal_date, cluster_size, total_\$.

**Acceptance criteria:**
- [ ] A reproducible script yields the historical event list
- [ ] Run is resumable / re-runnable without duplicating events

**Effort:** L · **Depends on:** SM-10

#### SM-15 — Forward-return + benchmark engine ⭐ *the experiment*
**What/why:** Measure whether the signal beats the market — correctly.
- For each event, set entry at the **next available close after the filing date** (no look-ahead). Compute forward 30/60/90-trading-day returns for the stock and for SPY; compute the excess return.

**Acceptance criteria:**
- [ ] Returns a tidy results frame (event × horizon × stock/benchmark/excess)
- [ ] Look-ahead is provably avoided (entry never precedes the public filing) and documented in code

**Effort:** L · **Depends on:** SM-14

#### SM-16 — Results analysis & verdict
**What/why:** Turn numbers into the thesis conclusion.
- Aggregate excess returns (mean, median, win rate, distribution); run a t-test or bootstrap; apply a simple transaction-cost haircut; render charts. Fold the conclusion into a new "Results" section of `THESIS.md`.

**Acceptance criteria:**
- [ ] A results notebook/page with the distribution and summary stats
- [ ] A one-paragraph honest verdict (supports / refutes H₁), written even if the answer is "no edge after costs"

**Effort:** M · **Depends on:** SM-15

### M6 — Polish & ship

#### SM-17 — Tests & CI
**What/why:** Prove correctness and keep data fresh automatically.
- `pytest` suite covering the parser, resolver, screener, and backtest math. GitHub Actions: run tests on push, and run the daily ingest on a cron schedule.

**Acceptance criteria:**
- [ ] CI is green on the main branch
- [ ] The scheduled ingest workflow runs and updates data

**Effort:** M · **Depends on:** SM-16

#### SM-18 — Deploy & document
**What/why:** Make it linkable and runnable by anyone.
- Deploy to Streamlit Community Cloud. Finalize `README.md`: what it does, architecture diagram, screenshots, a link to `THESIS.md`, setup instructions, and a clear "not financial advice" note.

**Acceptance criteria:**
- [ ] Public URL loads the working dashboard
- [ ] README lets a stranger clone, install, and run it; thesis is linked

**Effort:** M · **Depends on:** SM-17

---

## Suggested first week

The goal of week one is **data flowing end to end**, even if ugly:

1. **SM-01, SM-02** — scaffold and config (half a day)
2. **SM-03, SM-04** — compliant client + ticker/CIK resolver (one day)
3. **SM-05** — discover a day's Form 4s (half a day)
4. **SM-06** — parse one filing into transactions (the deep end — give it real time)
5. **SM-07, SM-08, SM-09** — classify, store, and wrap it in one ingest command

Hit that and the hardest, most distinctive part of the project is behind you. Everything after — screening, dashboard, backtest — builds on a working ingestion pipeline.

## Definition of done (every ticket)

- Code is committed with a clear message referencing the ticket (e.g. `SM-06: parse Form 4 Table I transactions`)
- Acceptance criteria are all checked
- Anything non-obvious has a test or a short note in the README
- It runs from a clean clone

## Stretch goals (after M6)

- Add **13F institutional holdings** as a second signal and a "what are funds accumulating" view
- **Sector and market-cap breakdowns** of where insider buying concentrates
- An **alerts** feature (email/Discord) when a fresh cluster buy appears
- Compare the signal's strength across **insider role** (CEO/CFO buys vs. directors)
