import json
from dataclasses import asdict

from ci_log_analyzer.models import (
    Summary,
)

MAX_LINES_SHOWN = 5

LABEL_WIDTH = 13
STATUS_WIDTH = 11
DURATION_WIDTH = 11
NAME_WIDTH = 18
COUNT_WIDTH = 12
INDENT = 2


def _format_pass_rate(rate: float | None) -> str:
    if rate is None:
        return "n/a"
    return f"{rate:.2%}"


def _format_line_numbers(numbers: list[int]) -> str:
    length = len(numbers)
    report_line = ", ".join(str(number) for number in numbers[:MAX_LINES_SHOWN])
    if length > MAX_LINES_SHOWN:
        more = length - MAX_LINES_SHOWN
        return f"{report_line} (+{more} more)"
    return report_line


def render_json(summary: Summary) -> str:
    data = asdict(summary)
    return json.dumps(data, indent=2, ensure_ascii=False)


def render_terminal(summary: Summary) -> str:
    lines = []
    title = "CI LOG ANALYZER"
    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")
    total = sum(summary.counts.values())
    lines.append(f"{'TESTS':<{LABEL_WIDTH}}{total}")
    for status, count in summary.counts.items():
        lines.append(f"{' '*INDENT}{status:<{STATUS_WIDTH}}{count}")
    pass_rate_result = _format_pass_rate(summary.pass_rate)
    lines.append(f"{'PASS RATE':<{LABEL_WIDTH}}{pass_rate_result}  (skipped tests excluded)")
    lines.append("")
    lines.append("SLOWEST TESTS")
    if not summary.slowest:
        lines.append("No tests found")
        lines.append("")
    else:
        
        lines.append(f"{' '*INDENT}{'DURATION':<{DURATION_WIDTH}}{'NAME':<{NAME_WIDTH}}STATUS")
        for test_case in summary.slowest:
            duration_text = f"{test_case.duration:.2f} s"
            lines.append(f"{' '*INDENT}{duration_text:<{DURATION_WIDTH}}{test_case.name:<{NAME_WIDTH}}{test_case.status}")
        lines.append("")
    lines.append("TOP ERRORS")
    if not summary.top_errors:
        lines.append("No errors found")
    else:
        for error in summary.top_errors:
            count_text = f"{error.count}x"
            lines.append(f"{' '*INDENT}{count_text:<12}{error.pattern}")
            line_format = _format_line_numbers(error.line_numbers)
            lines.append(f"{' '*(COUNT_WIDTH+INDENT)}lines {line_format}")
    return "\n".join(lines)
