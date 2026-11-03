import re

from ci_log_analyzer.models import LogEvent, LogLevel

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
PATH_PATTERN = re.compile(r"\S*[/\\]\S*")
LOG_LINE_PATTERN = re.compile(r"\b(ERROR|WARN(?:ING)?|FAIL(?:ED)?)\b[:\]\s]*(.*)")
TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})?"
)

KEYWORD_TO_LEVEL = {
    "ERROR": LogLevel.ERROR,
    "WARN": LogLevel.WARNING,
    "WARNING": LogLevel.WARNING,
    "FAIL": LogLevel.FAIL,
    "FAILED": LogLevel.FAIL,
}


def normalize_message(message: str) -> str:
    normalized_timestamp = TIMESTAMP_PATTERN.sub("<TIMESTAMP>", message)
    normalized_path = PATH_PATTERN.sub("<PATH>", normalized_timestamp)
    normalized_number = NUMBER_PATTERN.sub("<N>", normalized_path)

    return normalized_number


def _parse_line(line: str, line_number: int) -> LogEvent | None:
    match = LOG_LINE_PATTERN.search(line)
    if not match:
        return None
    level = KEYWORD_TO_LEVEL[match.group(1)]
    message = match.group(2).strip()
    return LogEvent(line_number, level, message)
