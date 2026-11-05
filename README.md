# CI Log Analyzer

Command-line tool that reads CI test results (JUnit XML) and build logs,
and produces a clear summary report.

## Status
Work in progress. Started October 2026.

## Done
- Project setup: `src` layout, packaging with `pyproject.toml`, lint and type checks
- Data model: test cases, test suites, log events and report (dataclasses + enums)
- JUnit XML parser:
  - supports both `<testsuites>` and single `<testsuite>` roots
  - maps passed, failed, error and skipped tests, with durations and messages
  - ignores unknown elements (`<system-out>`, `<properties>`)
  - raises a clear error on missing files, malformed XML or invalid data
- Unit and end-to-end tests on real pytest JUnit output
- Plain-text build log parser (error and warning detection, message normalisation for grouping)
- Analysis: totals, pass rate, slowest tests, most frequent errors
- Reports: Terminal summary, Markdown (tables) and JSON (full data)

## In progress
- Command-line interface

## Next steps
- GitHub Actions pipeline (lint, type check, tests)

## Tech
Python 3.12+, pytest, ruff, mypy