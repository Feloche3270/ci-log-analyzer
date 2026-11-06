import pytest

from ci_log_analyzer.analysis import (
    _all_test_cases,
    analyze,
    count_by_status,
    pass_rate,
    slowest_tests,
    top_errors,
)
from ci_log_analyzer.models import (
    ErrorGroup,
    LogEvent,
    LogLevel,
    Status,
    Summary,
    TestCase,
    TestSuiteResult,
)


@pytest.fixture
def list_of_suites():
    return [
        TestSuiteResult(
            "pytest",
            [TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0)],
        ),
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
                TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 0.0),
            ],
        ),
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.2),
                TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 0.1),
            ],
        ),
    ]


@pytest.fixture
def list_of_suites_without_skip_passed():
    return [
        TestSuiteResult("pytest"),
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
                TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 0.0),
            ],
        ),
    ]


# ---_all_test_cases----------------------------------------------------------------
def test_three_suites(list_of_suites):
    result = _all_test_cases(list_of_suites)
    assert result == [
        TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
        TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
        TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 0.0),
        TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.2),
        TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 0.1),
    ]


def test_suite_without_test_case():
    empty_list = [TestSuiteResult("pytest")]
    result = _all_test_cases(empty_list)
    assert result == []


def test_empty_list_suites():
    result = _all_test_cases([])
    assert result == []


def test_empty_then_one(list_of_suites_without_skip_passed):
    result = _all_test_cases(list_of_suites_without_skip_passed)
    assert result == [
        TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
        TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 0.0),
    ]


# ---count_by_status----------------------------------------------------------------
def test_count_mixed_statuses(list_of_suites):
    result = count_by_status(list_of_suites)
    assert result == {
        Status.PASSED: 1,
        Status.FAILED: 2,
        Status.ERROR: 1,
        Status.SKIPPED: 1,
    }


def test_skipped_absent(list_of_suites_without_skip_passed):
    result = count_by_status(list_of_suites_without_skip_passed)
    assert result == {
        Status.PASSED: 0,
        Status.FAILED: 1,
        Status.ERROR: 1,
        Status.SKIPPED: 0,
    }


def test_no_cases():
    result = count_by_status([])
    assert result == {
        Status.PASSED: 0,
        Status.FAILED: 0,
        Status.ERROR: 0,
        Status.SKIPPED: 0,
    }


# ---pass_rate----------------------------------------------------------------
def test_025_passed(list_of_suites):
    result = pass_rate(list_of_suites)
    assert result == 0.25


def test_only_skipped():
    list_of_suites_skipped = [
        TestSuiteResult("pytest"),
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.0),
                TestCase("test_skipped2", "tests.test_fixtures", Status.SKIPPED, 0.0),
            ],
        ),
    ]
    result = pass_rate(list_of_suites_skipped)
    assert result is None


def test_only_passed():
    list_of_suites_passed = [
        TestSuiteResult("pytest"),
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 0.0),
                TestCase("test_passed2", "tests.test_fixtures", Status.PASSED, 0.0),
            ],
        ),
    ]
    result = pass_rate(list_of_suites_passed)
    assert result == 1


def test_no_test_case():
    result = pass_rate([])
    assert result is None


def test_ratio_float():
    list_of_suites_2_out_3 = [
        TestSuiteResult("pytest"),
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 0.0),
                TestCase("test_passed2", "tests.test_fixtures", Status.PASSED, 0.0),
                TestCase("test_error", "tests.test_fixtures", Status.ERROR, 1.0),
            ],
        ),
    ]
    result = pass_rate(list_of_suites_2_out_3)
    assert result == pytest.approx(2 / 3)


# ---slowest_tests----------------------------------------------------------------
def test_slowest(list_of_suites):
    result = slowest_tests(list_of_suites, 3)
    assert result == [
        TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
        TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
        TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.2),
    ]


def test_n_larger_than_tests(list_of_suites):
    result = slowest_tests(list_of_suites, 10)
    assert result == [
        TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
        TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
        TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.2),
        TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 0.1),
        TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 0.0),
    ]


def test_same_duration():
    list_same_duration = [
        TestSuiteResult(
            "pytest",
            [
                TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 0.2),
                TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
                TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 1.6),
                TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 1.0),
                TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 2.0),
            ],
        )
    ]
    result = slowest_tests(list_same_duration, 4)
    assert result == [
        TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 2.0),
        TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 1.6),
        TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
        TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 1.0),
    ]


def test_no_test_case_slowest():
    result = slowest_tests([], 3)
    assert result == []


# ---top_errors----------------------------------------------------------------
def test_group_error():
    list_log_error = [
        LogEvent(
            9,
            LogLevel.ERROR,
            "Timeout after 12 s in /app/tests/test_smoke.py (job 50991)",
        ),
        LogEvent(
            16,
            LogLevel.ERROR,
            r"Timeout after 12.5 s in \app\tests\test_models.py (job 50996)",
        ),
    ]
    result = top_errors(list_log_error)
    assert result == [ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [9, 16])]


def test_warning_ignored():
    list_log_error = [
        LogEvent(8, LogLevel.WARNING, "Deprecated API used in src/ci_log_analyzer"),
        LogEvent(
            9,
            LogLevel.ERROR,
            "Timeout after 12 s in /app/tests/test_smoke.py (job 50991)",
        ),
        LogEvent(
            16,
            LogLevel.ERROR,
            r"Timeout after 12.5 s in \app\tests\test_models.py (job 50996)",
        ),
    ]
    result = top_errors(list_log_error)
    assert result == [ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [9, 16])]


def test_sort_by_count():
    list_log_error = [
        LogEvent(8, LogLevel.ERROR, "Deprecated API used in src/ci_log_analyzer"),
        LogEvent(
            9,
            LogLevel.ERROR,
            "Timeout after 12 s in /app/tests/test_smoke.py (job 50991)",
        ),
        LogEvent(14, LogLevel.FAIL, "test/test_models.py"),
        LogEvent(15, LogLevel.FAIL, "test/test_smokes.py"),
        LogEvent(
            16,
            LogLevel.ERROR,
            r"Timeout after 12.5 s in \app\tests\test_models.py (job 50996)",
        ),
        LogEvent(20, LogLevel.FAIL, "test/test_junit.py"),
    ]
    result = top_errors(list_log_error)
    assert result == [
        ErrorGroup("<PATH>", 3, [14, 15, 20]),
        ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [9, 16]),
        ErrorGroup("Deprecated API used in <PATH>", 1, [8]),
    ]


def test_first_appearance():
    list_log_error = [
        LogEvent(
            8,
            LogLevel.ERROR,
            r"Timeout after 12.5 s in \app\tests\test_models.py (job 50996)",
        ),
        LogEvent(9, LogLevel.FAIL, "test/test_models.py"),
        LogEvent(
            14,
            LogLevel.ERROR,
            "Timeout after 12 s in /app/tests/test_smoke.py (job 50991)",
        ),
        LogEvent(15, LogLevel.FAIL, "test/test_smokes.py"),
    ]

    result = top_errors(list_log_error)
    assert result == [
        ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [8, 14]),
        ErrorGroup("<PATH>", 2, [9, 15]),
    ]


def test_n_limit():
    list_log_error = [
        LogEvent(
            8,
            LogLevel.ERROR,
            r"Timeout after 12.5 s in \app\tests\test_models.py (job 50996)",
        ),
        LogEvent(9, LogLevel.FAIL, "test/test_models.py"),
        LogEvent(
            14,
            LogLevel.ERROR,
            "Timeout after 12 s in /app/tests/test_smoke.py (job 50991)",
        ),
        LogEvent(15, LogLevel.FAIL, "test/test_smokes.py"),
    ]
    result = top_errors(list_log_error, 1)
    assert result == [ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [8, 14])]
    assert len(result) == 1


def test_empty_log_error():
    result = top_errors([])
    assert result == []


def test_only_warning():
    list_log_error = [
        LogEvent(8, LogLevel.WARNING, "Deprecated API used in src/ci_log_analyzer")
    ]
    result = top_errors(list_log_error)
    assert result == []


# ---analyze----------------------------------------------------------------
def test_analyze(list_of_suites):
    list_log_error = [
        LogEvent(8, LogLevel.ERROR, "Deprecated API used in src/ci_log_analyzer"),
        LogEvent(
            9,
            LogLevel.ERROR,
            "Timeout after 12 s in /app/tests/test_smoke.py (job 50991)",
        ),
        LogEvent(14, LogLevel.FAIL, "test/test_models.py"),
        LogEvent(15, LogLevel.FAIL, "test/test_smokes.py"),
        LogEvent(
            16,
            LogLevel.ERROR,
            r"Timeout after 12.5 s in \app\tests\test_models.py (job 50996)",
        ),
        LogEvent(20, LogLevel.FAIL, "test/test_junit.py"),
    ]

    counts = {
        Status.PASSED: 1,
        Status.FAILED: 2,
        Status.ERROR: 1,
        Status.SKIPPED: 1,
    }
    pass_rate_result = 0.25

    slowest = [
        TestCase("test_fail2", "tests.test_fixtures", Status.FAILED, 1.4),
        TestCase("test_fail", "tests.test_fixtures", Status.FAILED, 1.0),
        TestCase("test_skipped", "tests.test_fixtures", Status.SKIPPED, 0.2),
        TestCase("test_passed", "tests.test_fixtures", Status.PASSED, 0.1),
        TestCase("test_value_error", "tests.test_fixtures", Status.ERROR, 0.0),
    ]

    top_errors_result = [
        ErrorGroup("<PATH>", 3, [14, 15, 20]),
        ErrorGroup("Timeout after <N> s in <PATH> (job <N>)", 2, [9, 16]),
        ErrorGroup("Deprecated API used in <PATH>", 1, [8]),
    ]

    result = analyze(list_of_suites, list_log_error)
    assert result == Summary(counts, pass_rate_result, slowest, top_errors_result)
