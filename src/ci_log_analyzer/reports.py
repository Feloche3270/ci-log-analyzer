import json
from dataclasses import asdict

from ci_log_analyzer.models import (
    Summary,
)

MAX_LINES_SHOWN = 5

LABEL_WIDTH_TERMINAL = 13
STATUS_WIDTH_TERMINAL = 11
DURATION_WIDTH_TERMINAL = 11
NAME_WIDTH_TERMINAL = 18
COUNT_WIDTH_TERMINAL = 12
INDENT_TERMINAL = 2


def _escape_cell(text: str) -> str:
    return text.replace("|", r"\|")


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
    lines.append(f"{'TESTS':<{LABEL_WIDTH_TERMINAL}}{total}")
    for status, count in summary.counts.items():
        lines.append(f"{' ' * INDENT_TERMINAL}{status:<{STATUS_WIDTH_TERMINAL}}{count}")
    pass_rate_result = _format_pass_rate(summary.pass_rate)
    lines.append(
        f"{'PASS RATE':<{LABEL_WIDTH_TERMINAL}}"
        f"{pass_rate_result}  (skipped tests excluded)"
    )
    lines.append("")
    lines.append("SLOWEST TESTS")
    if not summary.slowest:
        lines.append("No tests found")
    else:
        lines.append(
            f"{' ' * INDENT_TERMINAL}"
            f"{'DURATION':<{DURATION_WIDTH_TERMINAL}}"
            f"{'STATUS':<{STATUS_WIDTH_TERMINAL}}NAME"
        )
        for test_case in summary.slowest:
            duration_text = f"{test_case.duration:.2f} s"
            lines.append(
                f"{' ' * INDENT_TERMINAL}"
                f"{duration_text:<{DURATION_WIDTH_TERMINAL}}"
                f"{test_case.status:<{STATUS_WIDTH_TERMINAL}}{test_case.name}"
            )
    lines.append("")
    lines.append("TOP ERRORS")
    if not summary.top_errors:
        lines.append("No errors found")
    else:
        for error in summary.top_errors:
            count_text = f"{error.count}x"
            lines.append(
                f"{' ' * INDENT_TERMINAL}"
                f"{count_text:<{COUNT_WIDTH_TERMINAL}}{error.pattern}"
            )
            line_format = _format_line_numbers(error.line_numbers)
            lines.append(
                f"{' ' * (COUNT_WIDTH_TERMINAL + INDENT_TERMINAL)}lines {line_format}"
            )
    return "\n".join(lines)


def render_markdown(summary: Summary) -> str:
    lines = []
    lines.append("# CI LOG ANALYZER report")
    lines.append("")
    lines.append("## Tests by status")
    lines.append("")
    lines.append("| STATUS | COUNT |")
    lines.append("|---|---:|")
    for status, count in summary.counts.items():
        lines.append(f"| {status} | {count} |")
    lines.append("")
    pass_rate_result = _format_pass_rate(summary.pass_rate)
    lines.append(f"**Pass rate:** {pass_rate_result} (skipped tests excluded)")
    lines.append("")
    lines.append("## Slowest tests")
    if not summary.slowest:
        lines.append("No tests found")
    else:
        lines.append("")
        lines.append("| NAME | STATUS | DURATION |")
        lines.append("|---|---|---:|")
        for test_case in summary.slowest:
            test_case_name_escape = _escape_cell(test_case.name)
            duration_text = f"{test_case.duration:.2f} s"
            lines.append(
                f"| {test_case_name_escape} | {test_case.status} | {duration_text} |"
            )
    lines.append("")
    lines.append("## Top errors")
    if not summary.top_errors:
        lines.append("No errors found")
    else:
        lines.append("")
        max_length_pattern = 0
        max_length_lines = 0
        for error in summary.top_errors:
            if len(error.pattern) > max_length_pattern:
                max_length_pattern = len(error.pattern)
            if len(_format_line_numbers(error.line_numbers)) > max_length_lines:
                max_length_lines = len(_format_line_numbers(error.line_numbers))
        lines.append("| COUNT | PATTERN | LINES |")
        lines.append("|---:|---|---|")
        for error in summary.top_errors:
            pattern_backticks = "`" + error.pattern + "`"
            pattern_escape = _escape_cell(pattern_backticks)
            line_format = _format_line_numbers(error.line_numbers)
            lines.append(f"| {error.count} | {pattern_escape} | {line_format} |")
    return "\n".join(lines)
