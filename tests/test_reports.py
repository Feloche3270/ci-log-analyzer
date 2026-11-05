from ci_log_analyzer.reports import _format_line_numbers, _format_pass_rate

def test_passrate_percent():
    percent = 0.25
    result = _format_pass_rate(percent)
    assert result == "25.00%"


def test_passrate_none():
    result = _format_pass_rate(None)
    assert result == "n/a"


def test_format_line_under_five():
    list_numbers = [9, 10, 11, 12]
    result = _format_line_numbers(list_numbers)
    assert result == "9, 10, 11, 12"

def test_format_line_upper_five():
    list_numbers = [9, 10, 11, 12, 13, 14, 15]
    result = _format_line_numbers(list_numbers)
    assert result == "9, 10, 11, 12, 13 (+2 more)"