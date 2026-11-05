import json
from dataclasses import asdict

from ci_log_analyzer.models import (
    Summary,
)

MAX_LINES_SHOWN = 5


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
