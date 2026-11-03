from pathlib import Path

import pytest

from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import LogEvent, LogLevel
from ci_log_analyzer.parsers.textlog import (
    _parse_line,
    normalize_message,
    parse_textlog,
)


def test_timestamp_replace_before_numbers():
    result = normalize_message("at 2026-11-01 10:06:13")
    assert result == "at <TIMESTAMP>"


def test_iso_timestamp():
    result = normalize_message("at 2026-10-29T18:40:51.5Z")
    assert result == "at <TIMESTAMP>"


def test_unix_path():
    result = normalize_message("in /app/tests/test_smoke.py")
    assert result == "in <PATH>"


def test_windows_path():
    result = normalize_message(r"in \app\tests\test_models.py")
    assert result == "in <PATH>"


def test_integer_decimal():
    result = normalize_message("Timeout after 4.567 s (job 50996)")
    assert result == "Timeout after <N> s (job <N>)"


def test_grouping():
    result1 = normalize_message(
        "Timeout after 4.567 s in /app/tests/test_smoke.py (job 50996)"
    )
    result2 = normalize_message(
        r"Timeout after 5 s in \app\tests\test_models.py (job 456000)"
    )
    assert result1 == "Timeout after <N> s in <PATH> (job <N>)"
    assert result1 == result2


def test_untouched():
    result = normalize_message("Database connection lost")
    assert result == "Database connection lost"


def test_plain_format():
    result = _parse_line("2026-11-01 10:06:13 ERROR Timeout after 12 s", 9)
    assert result == LogEvent(9, LogLevel.ERROR, "Timeout after 12 s")


def test_maven():
    result = _parse_line("[ERROR] Failed to compile", 6)
    assert result == LogEvent(6, LogLevel.ERROR, "Failed to compile")


def test_python_logging():
    result = _parse_line("ERROR:root:Database connection lost", 7)
    assert result == LogEvent(7, LogLevel.ERROR, "root:Database connection lost")


def test_warn_warning():
    result1 = _parse_line("WARN Deprecated API used in src/utils.py", 3)
    result2 = _parse_line("WARNING Deprecated API used in src/ci_log_analyzer", 8)
    assert result1 is not None
    assert result2 is not None
    assert result1.level is LogLevel.WARNING
    assert result2.level is LogLevel.WARNING


def test_pytest_fail():
    result = _parse_line("FAILED tests/test_demo_fail.py::test_fail - assert 1 == 2", 1)
    assert result is not None
    assert result.level is LogLevel.FAIL


def test_space_end_msg():
    result = _parse_line("ERROR Failed to compile ", 6)
    assert result is not None
    assert result.message == "Failed to compile"


@pytest.mark.parametrize(
    ("line"),
    [
        ("INFO Starting build"),
        (""),
        ("FAILURES"),
        ("test_error_handling"),
        ("TEST_ERROR_HANDLING"),
        ("1 failed, 1 passed"),
    ],
)
def test_none_result(line):
    result = _parse_line(line, 1)
    assert result is None


@pytest.mark.parametrize(
    ("level", "loglevel"),
    [
        ("ERROR", LogLevel.ERROR),
        ("WARN", LogLevel.WARNING),
        ("WARNING", LogLevel.WARNING),
        ("FAIL", LogLevel.FAIL),
        ("FAILED", LogLevel.FAIL),
    ],
)
def test_level_result(level, loglevel):
    result = _parse_line(level, 1)
    assert result is not None
    assert result.level is loglevel


def test_length_logevent():
    path1 = Path(__file__).parent / "fixtures/build.log"
    result = parse_textlog(path1)
    assert len(result) == 16


def test_exact_logevent():
    path1 = Path(__file__).parent / "fixtures/build.log"
    result = parse_textlog(path1)
    assert result[0] == LogEvent(
        3, LogLevel.WARNING, "Deprecated API used in src/utils.py"
    )
    assert result[3] == LogEvent(7, LogLevel.ERROR, "root:Database connection lost")
    assert result[13] == LogEvent(19, LogLevel.ERROR, "root")


def test_pytest_output():
    path1 = Path(__file__).parent / "fixtures/pytest_output.log"
    result = parse_textlog(path1)
    assert result[0] == LogEvent(
        11, LogLevel.FAIL, "tests/test_demo_fail.py::test_fail - assert 1 == 2"
    )


def test_empty_file(tmp_path):
    file = tmp_path / "false_textlog.log"
    file.write_text("", encoding="utf-8")
    result = parse_textlog(file)
    assert result == []


def test_no_level_line(tmp_path):
    content = (
        "2026-11-01 10:01:12 INFO Starting build\n"
        "2026-11-01 10:01:13 INFO Compiling 350 files\n"
        "2026-11-01 10:01:21 INFO Build finished with 1 error\n"
        "2026-11-01 10:06:38 INFO "
    )
    file = tmp_path / "false_textlog.log"
    file.write_text(content, encoding="utf-8")
    result = parse_textlog(file)
    assert result == []


def test_textlog_not_valid_path():
    path = Path(__file__).parent / "false_path_textlog.log"
    with pytest.raises(ParseError, match="cannot be found"):
        parse_textlog(path)


def test_textlog_directory_raise(tmp_path):
    path = tmp_path
    with pytest.raises(ParseError, match="cannot be opened"):
        parse_textlog(path)


def test_invalid_utf8(tmp_path):
    file = tmp_path / "false_textlog.log"
    file.write_bytes(b"\xff\xfe invalid")
    with pytest.raises(ParseError, match="a byte isn't valid UTF-8"):
        parse_textlog(file)
