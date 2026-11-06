import json
from pathlib import Path

import pytest

from ci_log_analyzer.cli import _exit_code, _load, build_parser, main
from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import LogLevel, Status, Summary


@pytest.fixture
def path_junit():
    return Path(__file__).parent / "fixtures/junit_mixed.xml"


@pytest.fixture
def path_textlog():
    return Path(__file__).parent / "fixtures/build.log"


@pytest.fixture
def path_pytestlog():
    return Path(__file__).parent / "fixtures/pytest_output.log"


# ---build_parser----------------------------------------------------------------
def test_parser_defaults(path_junit):
    parser = build_parser()
    result = parser.parse_args(["analyze", str(path_junit)])
    assert result.command == "analyze"
    assert result.files == [path_junit]
    assert result.format == "terminal"
    assert result.output is None
    assert result.top == 5
    assert result.fail_on_failures is False


def test_parser_all_options(path_junit, tmp_path):
    parser = build_parser()
    result = parser.parse_args(
        [
            "analyze",
            str(path_junit),
            "--format",
            "json",
            "--output",
            str(tmp_path / "out.md"),
            "--top",
            "2",
            "--fail-on-failures",
        ]
    )
    assert result.command == "analyze"
    assert result.files == [path_junit]
    assert result.format == "json"
    assert result.output == (tmp_path / "out.md")
    assert result.top == 2
    assert result.fail_on_failures is True


def test_parser_invalid_format_exits(path_junit):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(
            [
                "analyze",
                str(path_junit),
                "--format",
                "pdf",
                "--top",
                "2",
                "--fail-on-failures",
            ]
        )
    assert exc_info.value.code == 2


def test_parser_no_files_exits():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["analyze"])
    assert exc_info.value.code == 2


# ---_load----------------------------------------------------------------
def test_load_junit_and_log(path_junit, path_textlog):
    suites, events = _load([path_junit, path_textlog])
    assert len(suites) == 1
    assert len(events) == 16


def test_load_uppercase_xml_suffix(tmp_path):
    content = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<testsuite name='pytest' tests='1' time='0.075'>"
        "<testcase classname='tests.test_fixtures' name='test_pass' time='0.001'/>"
        "</testsuite>"
    )
    suites_path = tmp_path / "report.XML"
    suites_path.write_text(content, encoding="utf-8")

    suites, events = _load([suites_path])
    assert len(suites) == 1
    assert len(events) == 0


def test_load_two_logs(path_textlog, path_pytestlog):
    suites, events = _load([path_textlog, path_pytestlog])
    assert events[0].level is LogLevel.WARNING
    assert events[-1].level is LogLevel.FAIL
    assert len(events) == 17


def test_load_missing_file_raises():
    paths_test = Path(__file__).parent / "false_path_textlog.log"
    with pytest.raises(ParseError, match="cannot be found"):
        _load([paths_test])


# ---_exit_code----------------------------------------------------------------
def test_exit_code_flag_off_with_failures():
    counts = {
        Status.PASSED: 1,
        Status.FAILED: 2,
        Status.ERROR: 1,
        Status.SKIPPED: 1,
    }
    result = _exit_code(Summary(counts, None), False)
    assert result == 0


def test_exit_code_flag_on_no_failures():
    counts = {
        Status.PASSED: 1,
        Status.FAILED: 0,
        Status.ERROR: 0,
        Status.SKIPPED: 1,
    }
    result = _exit_code(Summary(counts, None), True)
    assert result == 0


def test_exit_code_flag_on_failed():
    counts = {
        Status.PASSED: 1,
        Status.FAILED: 1,
        Status.ERROR: 0,
        Status.SKIPPED: 1,
    }
    result = _exit_code(Summary(counts, None), True)
    assert result == 1


def test_exit_code_flag_on_error_only():
    counts = {
        Status.PASSED: 1,
        Status.FAILED: 0,
        Status.ERROR: 1,
        Status.SKIPPED: 1,
    }
    result = _exit_code(Summary(counts, None), True)
    assert result == 1


# ---main----------------------------------------------------------------
def test_main_terminal_report(path_textlog, path_junit, capsys):
    argv = ["analyze", str(path_textlog), str(path_junit), "--format", "terminal"]
    result = main(argv)
    captured = capsys.readouterr()
    captured_split = captured.out.splitlines()
    assert result == 0
    assert "CI LOG ANALYZER" in captured.out
    assert "TESTS        4" in captured_split


def test_main_markdown_report(path_textlog, path_junit, capsys):
    argv = ["analyze", str(path_textlog), str(path_junit), "--format", "md"]
    result = main(argv)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.startswith("# CI LOG ANALYZER")


def test_main_json_report(path_textlog, path_junit, capsys):
    argv = ["analyze", str(path_textlog), str(path_junit), "--format", "json"]
    result = main(argv)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert result == 0
    assert data["counts"]["passed"] == 1


def test_main_top_option(path_textlog, path_junit, capsys):
    argv = [
        "analyze",
        str(path_textlog),
        str(path_junit),
        "--format",
        "json",
        "--top",
        "1",
    ]
    result = main(argv)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert result == 0
    assert len(data["slowest"]) == 1
    assert len(data["top_errors"]) == 1


def test_main_output_file(path_textlog, path_junit, capsys, tmp_path):
    argv = [
        "analyze",
        str(path_textlog),
        str(path_junit),
        "--format",
        "terminal",
        "--output",
        str(tmp_path / "report.txt"),
        "--top",
        "1",
    ]
    result = main(argv)
    captured = capsys.readouterr()
    assert result == 0
    assert "CI LOG ANALYZER" in (tmp_path / "report.txt").read_text(encoding="utf-8")
    assert (tmp_path / "report.txt").read_text(encoding="utf-8").endswith("\n")
    assert captured.out == ""


def test_main_fail_on_failures(path_junit):
    argv = [
        "analyze",
        str(path_junit),
        "--fail-on-failures",
    ]
    result = main(argv)
    assert result == 1


def test_main_all_passed_with_flag(tmp_path):
    content = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<testsuite name='pytest' tests='1' time='0.075'>"
        "<testcase classname='tests.test_fixtures' name='test_pass' time='0.001'/>"
        "</testsuite>"
    )
    suites_path = tmp_path / "report.XML"
    suites_path.write_text(content, encoding="utf-8")
    argv = [
        "analyze",
        str(tmp_path / "report.XML"),
        "--format",
        "terminal",
        "--top",
        "1",
        "--fail-on-failures",
    ]
    result = main(argv)
    assert result == 0


def test_main_missing_file(tmp_path, capsys):
    argv = [
        "analyze",
        str(tmp_path / "report_false_path.xml"),
        "--format",
        "terminal",
    ]
    result = main(argv)
    captured = capsys.readouterr()
    assert result == 2
    assert "cilog: error: " in captured.err
    assert str(tmp_path / "report_false_path.xml") in captured.err
    assert captured.out == ""
