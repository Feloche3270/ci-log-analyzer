import json
from dataclasses import asdict

from ci_log_analyzer.models import (
    LogEvent,
    LogLevel,
    Report,
    Status,
    TestCase,
    TestSuiteResult,
)

case_1 = TestCase(
    "Failed Case",
    "test.test_failed",
    Status.FAILED,
    1.618,
    "Test have failed in 1.613 s",
)
case_2 = TestCase(
    "Failed Case",
    "test.test_failed",
    Status.FAILED,
    1.618,
    "Test have failed in 1.613 s",
)


def test_identical():
    assert case_1 == case_2


suite_1 = TestSuiteResult("test_suite_failed", [case_1, case_2])
suite_2 = TestSuiteResult("test_suite_failed_2")


def test_list_empty():
    assert suite_1.test_cases != []
    assert suite_2.test_cases == []


def test_status():
    dict_case = asdict(case_1)
    data = json.dumps(dict_case)
    loaded = json.loads(data)
    assert loaded["status"] == "failed"


log_1 = LogEvent(1, LogLevel.ERROR, "Error log")


def test_read_log_event():
    assert log_1 is not None


report_1 = Report([suite_1, suite_2], [log_1])


def test_report():
    assert report_1 is not None
