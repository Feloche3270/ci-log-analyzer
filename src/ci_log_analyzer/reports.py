MAX_LINES_SHOWS = 5


def _format_pass_rate(rate: float | None) -> str:
    if rate is None:
        return "n/a"
    return f"{rate:.2%}"

def _format_line_numbers(numbers: list[int]) -> str:
    length = len(numbers)
    report_line = ", ".join(str(number) for number in numbers[:MAX_LINES_SHOWS])
    if length > MAX_LINES_SHOWS:
        more = length - MAX_LINES_SHOWS
        return f"{report_line} (+{more} more)"
    return report_line