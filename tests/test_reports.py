import json

import pytest

from ci_log_analyzer.models import ErrorGroup, Status, Summary, TestCase
from ci_log_analyzer.reports import _format_line_numbers, _format_pass_rate, render_json


@pytest.fixture
def known_summary():
    counts = {
        Status.PASSED: 1,
        Status.FAILED: 2,
        Status.ERROR: 1,
        Status.SKIPPED: 1,
    }
    pass_rate = 0.25
    slowest = [
        TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
        TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
        TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.2),
    ]
    top_errors = [
        ErrorGroup("<PATH>", 3, [14, 15, 20]),
        ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [9, 16]),
        ErrorGroup("Deprecated API used in <PATH>", 1, [8]),
    ]
    return Summary(counts, pass_rate, slowest, top_errors)


@pytest.fixture
def empty_summary():
    counts = {
        Status.PASSED: 0,
        Status.FAILED: 0,
        Status.ERROR: 0,
        Status.SKIPPED: 0,
    }
    pass_rate = None
    return Summary(counts, pass_rate)


def test_passrate_percent():
    percent = 0.25
    result = _format_pass_rate(percent)
    assert result == "25.00%"


def test_passrate_none():
    result = _format_pass_rate(None)
    assert result == "n/a"


def test_format_line_less_than_five():
    list_numbers = [9]
    result = _format_line_numbers(list_numbers)
    assert result == "9"


def test_format_line_more_than_five():
    list_numbers = [9, 10, 11, 12, 13, 14, 15]
    result = _format_line_numbers(list_numbers)
    assert result == "9, 10, 11, 12, 13 (+2 more)"


def test_format_line_exactly_five():
    list_numbers = [9, 10, 11, 12, 13]
    result = _format_line_numbers(list_numbers)
    assert result == "9, 10, 11, 12, 13"


def test_format_line_empty():
    result = _format_line_numbers([])
    assert result == ""


def test_json_content(known_summary):
    result = render_json(known_summary)
    assert json.loads(result) == {
        "counts": {"passed": 1, "failed": 2, "error": 1, "skipped": 1},
        "pass_rate": 0.25,
        "slowest": [
            {
                "name": "test_fail2",
                "classname": "tests.test_fixtures",
                "status": "failed",
                "duration": 1.4,
                "message": None,
            },
            {
                "name": "test_fail",
                "classname": "tests.test_fixtures",
                "status": "failed",
                "duration": 1.0,
                "message": None,
            },
            {
                "name": "test_skipped",
                "classname": "tests.test_fixtures",
                "status": "skipped",
                "duration": 0.2,
                "message": None,
            },
        ],
        "top_errors": [
            {"pattern": "<PATH>", "count": 3, "line_numbers": [14, 15, 20]},
            {
                "pattern": "Timeout after <N> s in <PATH> (job <N>)",
                "count": 2,
                "line_numbers": [9, 16],
            },
            {
                "pattern": "Deprecated API used in <PATH>",
                "count": 1,
                "line_numbers": [8],
            },
        ],
    }


def test_pass_rate_none(empty_summary):
    result = render_json(empty_summary)
    result_loaded = json.loads(result)
    assert result_loaded["pass_rate"] is None


def test_slowest_top_errors_empty(empty_summary):
    result = render_json(empty_summary)
    result_loaded = json.loads(result)
    assert result_loaded["slowest"] == []
    assert result_loaded["top_errors"] == []
