"""Discover Form 4 filings from EDGAR's daily index.

For a given date, EDGAR publishes a master index of every filing that day at:

    https://www.sec.gov/Archives/edgar/daily-index/{year}/QTR{q}/master.{YYYYMMDD}.idx

It's pipe-delimited: CIK|Company Name|Form Type|Date Filed|Filename.
This module fetches it, keeps only the Form 4s (insider transactions), and
returns lightweight references that SM-06 will turn into parsed transactions.

Smoke test:  python -m smart_money.discover 2026-06-12
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

from . import client, config


@dataclass(frozen=True)
class Form4Filing:
    """A reference to one Form 4 filing — enough to fetch it later."""

    cik: int
    company: str
    date_filed: str
    accession: str            # e.g. "0000320193-26-000077"

    @property
    def accession_nodashes(self) -> str:
        return self.accession.replace("-", "")

    @property
    def filing_dir_url(self) -> str:
        """Directory holding the filing's documents (SM-06 looks here for the XML)."""
        return f"{config.ARCHIVES_BASE}/{self.cik}/{self.accession_nodashes}/"


def _coerce_date(d: date | str) -> date:
    return d if isinstance(d, date) else datetime.strptime(d, "%Y-%m-%d").date()


def _daily_master_url(d: date) -> str:
    quarter = (d.month - 1) // 3 + 1
    return f"{config.DAILY_INDEX_BASE}/{d.year}/QTR{quarter}/master.{d:%Y%m%d}.idx"


def form4_filings_for_date(
    d: date | str,
    include_amendments: bool = False,
    cli: client.EdgarClient | None = None,
) -> list[Form4Filing]:
    """Return every Form 4 filed on date `d` (empty list on weekends/holidays)."""
    d = _coerce_date(d)
    cli = cli or client.default_client
    wanted = {"4", "4/A"} if include_amendments else {"4"}

    try:
        text = cli.get(_daily_master_url(d)).text
    except requests.HTTPError as exc:
        resp = getattr(exc, "response", None)
        if resp is not None and resp.status_code == 404:
            return []          # no index for this day -> nothing was filed
        raise

    filings: list[Form4Filing] = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) != 5:
            continue
        cik_s, company, form_type, date_filed, filename = (p.strip() for p in parts)
        if not cik_s.isdigit() or form_type not in wanted:
            continue
        accession = Path(filename).stem        # ".../0000320193-26-000077.txt" -> stem
        filings.append(Form4Filing(int(cik_s), company, date_filed, accession))
    return filings


def form4_filings_for_range(
    start: date | str,
    end: date | str,
    include_amendments: bool = False,
    cli: client.EdgarClient | None = None,
) -> list[Form4Filing]:
    """Form 4 filings across an inclusive date range."""
    start, end = _coerce_date(start), _coerce_date(end)
    out: list[Form4Filing] = []
    day = start
    while day <= end:
        out.extend(form4_filings_for_date(day, include_amendments, cli))
        day += timedelta(days=1)
    return out


if __name__ == "__main__":
    import sys

    if not config.user_agent_is_configured():
        raise SystemExit("Set SEC_USER_AGENT first (see README).")

    target = sys.argv[1] if len(sys.argv) > 1 else (date.today() - timedelta(days=1)).isoformat()
    filings = form4_filings_for_date(target)
    print(f"{target}: found {len(filings):,} Form 4 filings.")
    if not filings:
        print(
            "(Weekends, holidays, and the current day before ~10pm ET have no index yet. "
            "Try a recent weekday, e.g. python -m smart_money.discover 2026-06-12)"
        )
    for f in filings[:10]:
        print(f"  CIK {f.cik:>10}  {f.accession}  {f.company}")
    if len(filings) > 10:
        print(f"  ... and {len(filings) - 10:,} more")