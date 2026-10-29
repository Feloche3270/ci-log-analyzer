from dataclasses import dataclass, field
from enum import StrEnum, auto


class Status(StrEnum):
    PASSED = auto()
    FAILED = auto()
    ERROR = auto()
    SKIPPED = auto()


@dataclass
class TestCase:
    name: str
    classname: str
    status: Status
    duration: float
    message: str | None = None


@dataclass
class TestSuiteResult:
    name: str
    test_cases: list[TestCase] = field(default_factory=list)


class LogLevel(StrEnum):
    ERROR = auto()
    WARNING = auto()
    FAIL = auto()


@dataclass
class LogEvent:
    line_number: int
    level: LogLevel
    message: str


@dataclass
class Report:
    suites: list[TestSuiteResult] = field(default_factory=list)
    log_events: list[LogEvent] = field(default_factory=list)
