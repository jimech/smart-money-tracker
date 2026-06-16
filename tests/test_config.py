from smart_money import config


def test_headers_include_user_agent():
    h = config.headers()
    assert "User-Agent" in h
    assert h["User-Agent"]


def test_cik_is_zero_padded_to_ten_digits():
    assert config.cik10(320193) == "0000320193"
    assert len(config.cik10(1)) == 10


def test_signal_defaults_are_sane():
    assert config.CLUSTER_MIN_INSIDERS >= 1
    assert config.CLUSTER_WINDOW_DAYS >= 1
    assert config.CLUSTER_MIN_USD > 0
