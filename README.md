# CI Log Analyzer
[![CI](https://github.com/Feloche3270/ci-log-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Feloche3270/ci-log-analyzer/actions/workflows/ci.yml)

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
- Plain-text build log parser (error and warning detection, message normalisation for grouping)
- Analysis: totals, pass rate, slowest tests, most frequent errors
- Reports: Terminal summary, Markdown (tables) and JSON (full data)
- Command-line interface: `cilog analyze`, with format, output, top-N and exit-code options, coverage 95%
- Unit and end-to-end tests on real pytest JUnit output and build logs
- GitHub Actions pipeline on Python 3.12–3.14 (lint, format, type check, tests), with the tool's own report in the job summary

## In progress
- Usage guide and design choices

## Next steps
- Optional: AI-generated summary of the top failures

## Tech
Python 3.12+, pytest, ruff, mypy, GitHub Actions