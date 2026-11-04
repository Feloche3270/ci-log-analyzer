from collections import Counter, defaultdict

from ci_log_analyzer.models import (
    ErrorGroup,
    LogEvent,
    LogLevel,
    Status,
    Summary,
    TestCase,
    TestSuiteResult,
)
from ci_log_analyzer.parsers.textlog import normalize_message

ACCEPTED_LEVELS = {LogLevel.ERROR, LogLevel.FAIL}


def _all_test_cases(suites: list[TestSuiteResult]) -> list[TestCase]:
    return [test_case for test_suite in suites for test_case in test_suite.test_cases]


def count_by_status(suites: list[TestSuiteResult]) -> dict[Status, int]:
    all_test_cases = _all_test_cases(suites)
    counts = Counter(test_case.status for test_case in all_test_cases)
    return {member: counts[member] for member in Status}


def pass_rate(suites: list[TestSuiteResult]) -> float | None:
    counts = count_by_status(suites)
    total = sum(counts.values())
    denominator = total - counts[Status.SKIPPED]
    if denominator <= 0:
        return None
    pass_rate_number = counts[Status.PASSED] / denominator
    return pass_rate_number


def slowest_tests(suites: list[TestSuiteResult], n: int = 5) -> list[TestCase]:
    all_test_cases = _all_test_cases(suites)
    return sorted(
        all_test_cases, key=lambda test_case: test_case.duration, reverse=True
    )[:n]


def top_errors(events: list[LogEvent], n: int = 5) -> list[ErrorGroup]:
    msg_pattern_to_line = defaultdict(list)
    for log_event in events:
        if log_event.level in ACCEPTED_LEVELS:
            pattern = normalize_message(log_event.message)
            msg_pattern_to_line[pattern].append(log_event.line_number)
    groups = [
        ErrorGroup(msg_pattern, len(line_numbers), line_numbers)
        for msg_pattern, line_numbers in msg_pattern_to_line.items()
    ]
    return sorted(groups, key=lambda group: group.count, reverse=True)[:n]


def analyze(suites: list[TestSuiteResult], events: list[LogEvent], n: int = 5):
    counts = count_by_status(suites)
    pass_rate_result = pass_rate(suites)
    slowest = slowest_tests(suites, n)
    top_errors_result = top_errors(events, n)
    return Summary(counts, pass_rate_result, slowest, top_errors_result)
