import argparse
import sys
from pathlib import Path

from ci_log_analyzer.analysis import analyze
from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import Status, Summary
from ci_log_analyzer.parsers.junit import parse_junit
from ci_log_analyzer.parsers.textlog import parse_textlog
from ci_log_analyzer.reports import render_json, render_markdown, render_terminal

MAPPING_FORMAT = {
    "terminal": render_terminal,
    "md": render_markdown,
    "json": render_json,
}

JUNIT_SUFFIX = ".xml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cilog", description="Summarize CI test results and build logs"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze logs")
    analyze_parser.add_argument(
        "files", nargs="+", type=Path, help="JUnit XML reports and text build logs"
    )
    analyze_parser.add_argument(
        "--format",
        choices=list(MAPPING_FORMAT),
        default="terminal",
        help="Format of file rendered",
    )
    analyze_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to this file instead of printing it",
    )
    analyze_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of error in the top errors and slowests sections",
    )
    analyze_parser.add_argument("--fail-on-failures", action="store_true")
    return parser


def _load(paths: list[Path]) -> tuple[list, list]:
    list_suites = []
    list_events = []
    for path in paths:
        if path.suffix.lower() == JUNIT_SUFFIX:
            list_suites.extend(parse_junit(path))
        else:
            list_events.extend(parse_textlog(path))
    return list_suites, list_events


def _exit_code(summary: Summary, fail_on_failures: bool) -> int:
    if not fail_on_failures:
        return 0
    return 1 if summary.counts[Status.FAILED] + summary.counts[Status.ERROR] >= 1 else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        suites, events = _load(args.files)
    except ParseError as err:
        print(f"cilog: error: {err}", file=sys.stderr)
        return 2
    summary = analyze(suites, events, args.top)
    renderer = MAPPING_FORMAT[args.format]
    result = renderer(summary)
    if args.output is None:
        print(result)
    else:
        args.output.write_text(result + "\n", encoding="utf-8")
    return _exit_code(summary, args.fail_on_failures)
