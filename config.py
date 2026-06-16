"""Central configuration for Smart Money Tracker.

One place for everything the rest of the package needs: the SEC-required
request identity, base URLs, a polite rate limit, the default signal
parameters from THESIS.md, and local paths.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- SEC compliance -------------------------------------------------------
# The SEC requires every request to identify you with a real User-Agent that
# includes a contact email. Requests without one (or using example.com) get
# blocked. Set this via an environment variable so you never commit your email:
#
#     export SEC_USER_AGENT="Your Name your-real-email@gmail.com"
#
# The fallback below is a placeholder ONLY and will be rejected by the SEC.
SEC_USER_AGENT: str = os.environ.get(
    "SEC_USER_AGENT",
    "Smart Money Tracker REPLACE-ME@example.com",
)

# SEC allows up to 10 requests/second across all your machines. Stay under it.
MAX_REQUESTS_PER_SEC: int = 8


def headers() -> dict[str, str]:
    """Standard headers for every SEC request."""
    return {
        "User-Agent": SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    }


def user_agent_is_configured() -> bool:
    """True once the placeholder email has been replaced with a real one."""
    return "REPLACE-ME@example.com" not in SEC_USER_AGENT


# --- SEC endpoints (all free, no API key) ---------------------------------
SEC_WWW_BASE: str = "https://www.sec.gov"
SEC_DATA_BASE: str = "https://data.sec.gov"

COMPANY_TICKERS_URL: str = f"{SEC_WWW_BASE}/files/company_tickers.json"
SUBMISSIONS_URL: str = SEC_DATA_BASE + "/submissions/CIK{cik10}.json"
DAILY_INDEX_BASE: str = f"{SEC_WWW_BASE}/Archives/edgar/daily-index"
ARCHIVES_BASE: str = f"{SEC_WWW_BASE}/Archives/edgar/data"


def cik10(cik: int | str) -> str:
    """Zero-pad a CIK to the 10-digit form EDGAR expects (e.g. 320193 -> '0000320193')."""
    return str(int(cik)).zfill(10)


# --- Signal defaults (see THESIS.md) --------------------------------------
CLUSTER_MIN_INSIDERS: int = 3      # N: distinct insiders buying...
CLUSTER_WINDOW_DAYS: int = 10      # W: ...within this many trading days...
CLUSTER_MIN_USD: int = 100_000     # X: ...with combined purchase value above this.

# --- Storage --------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
DB_PATH: Path = DATA_DIR / "smart_money.db"
