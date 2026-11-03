from ci_log_analyzer.parsers.textlog import normalize_message


def test_timestamp_replace_before_numbers():
    result = normalize_message("at 2026-11-01 10:06:13")
    assert result == "at <TIMESTAMP>"


def test_iso_timestamp():
    normalize_iso_timestamp = normalize_message("at 2026-10-29T18:40:51.5Z")
    assert normalize_iso_timestamp == "at <TIMESTAMP>"


def test_unix_path():
    result = normalize_message("in /app/tests/test_smoke.py")
    assert result == "in <PATH>"


def test_windows_path():
    result = normalize_message(r"in \app\tests\test_models.py")
    assert result == "in <PATH>"


def test_integer_decimal():
    result = normalize_message("Timeout after 4.567 s (job 50996)")
    assert result == "Timeout after <N> s (job <N>)"


def test_grouping():
    result1 = normalize_message("Timeout after 4.567 s in ... (job 50996)")
    result2 = normalize_message("Timeout after 5 s in ... (job 456000)")
    assert result1 == "Timeout after <N> s in ... (job <N>)"
    assert result1 == result2


def test_untouched():
    result = normalize_message("Database connection lost")
    assert result == "Database connection lost"
