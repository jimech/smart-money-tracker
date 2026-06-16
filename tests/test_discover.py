import requests

from smart_money.discover import form4_filings_for_date

SAMPLE_IDX = """Description:           Master Index of EDGAR Dissemination Feed
Last Data Received:    June 12, 2026
Comment:               webmaster@sec.gov

CIK|Company Name|Form Type|Date Filed|Filename
--------------------------------------------------------------------------------
320193|Apple Inc.|4|2026-06-12|edgar/data/320193/0000320193-26-000077.txt
789019|MICROSOFT CORP|10-Q|2026-06-12|edgar/data/789019/0000789019-26-000050.txt
1318605|Tesla, Inc.|4/A|2026-06-12|edgar/data/1318605/0001318605-26-000033.txt
1045810|NVIDIA CORP|4|2026-06-12|edgar/data/1045810/0001045810-26-000099.txt
"""


class FakeResp:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


class FakeClient:
    def __init__(self, text=None, status_code=200):
        self._text = text
        self._status = status_code

    def get(self, url, **kw):
        if self._status == 404:
            raise requests.HTTPError("404", response=FakeResp(404))
        return FakeResp(200, self._text)


def test_keeps_only_form4_by_default():
    filings = form4_filings_for_date("2026-06-12", cli=FakeClient(SAMPLE_IDX))
    assert [f.cik for f in filings] == [320193, 1045810]


def test_includes_amendments_when_asked():
    filings = form4_filings_for_date(
        "2026-06-12", include_amendments=True, cli=FakeClient(SAMPLE_IDX)
    )
    assert {f.cik for f in filings} == {320193, 1045810, 1318605}


def test_extracts_accession_and_urls():
    apple = form4_filings_for_date("2026-06-12", cli=FakeClient(SAMPLE_IDX))[0]
    assert apple.accession == "0000320193-26-000077"
    assert apple.accession_nodashes == "000032019326000077"
    assert apple.filing_dir_url.endswith("/320193/000032019326000077/")


def test_no_index_returns_empty():
    assert form4_filings_for_date("2026-06-14", cli=FakeClient(status_code=404)) == []