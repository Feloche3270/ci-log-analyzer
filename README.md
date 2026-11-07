# CI Log Analyzer
[![CI](https://github.com/Feloche3270/ci-log-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/Feloche3270/ci-log-analyzer/actions/workflows/ci.yml)

Command-line tool that reads CI test results (JUnit XML) and build logs,
and produces a clear summary: test counts, pass rate, slowest tests and
the most frequent errors. Output as a terminal summary, Markdown or JSON.

## Install

Requires Python 3.12 or newer.

```bash
git clone https://github.com/Feloche3270/ci-log-analyzer.git
cd ci-log-analyzer
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

```bash
cilog analyze <files...> [--format terminal|md|json] [--output FILE] [--top N] [--fail-on-failures]
```

Files ending in `.xml` are read as JUnit reports; any other file is read as a text build log.
Several files can be combined in one run.

```bash
# Terminal summary of test results and a build log
cilog analyze tests/fixtures/junit_mixed.xml tests/fixtures/build.log

# Markdown report saved to a file
cilog analyze tests/fixtures/junit_mixed.xml --format md --output report.md

# JSON with only the top 3 slowest tests and errors
cilog analyze tests/fixtures/junit_mixed.xml tests/fixtures/build.log --format json --top 3
```

| Option | Default | Description |
|---|---|---|
| `--format` | `terminal` | `terminal`, `md` or `json` |
| `--output` | — | write the report to a file instead of printing it |
| `--top` | `5` | number of slowest tests and top errors shown |
| `--fail-on-failures` | off | exit with code 1 if any test failed or errored |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | report produced (default, even when tests failed) |
| `1` | failed or errored tests, only with `--fail-on-failures` |
| `2` | invalid arguments, or a file that cannot be read or parsed |

### Example output

```text
CI LOG ANALYZER
===============

TESTS        4
  passed     1
  failed     1
  error      1
  skipped    1
PASS RATE    33.33%  (skipped tests excluded)

SLOWEST TESTS
  DURATION   STATUS     NAME
  0.00 s     passed     test_pass
  0.00 s     failed     test_fail
  0.00 s     error      test_with_value_error
  0.00 s     skipped    test_skip

TOP ERRORS
  8x          Timeout after <N> s in <PATH> (job <N>)
              lines 9, 10, 11, 12, 13 (+3 more)
  1x          Test failed : test_logout (timeout after <N> s)
              lines 4
  1x          Failed to compile (timeout after <N> s)
              lines 6
  1x          root:Database connection lost
              lines 7
  1x          root
              lines 19
```

## In CI

This repository runs its own tool: the GitHub Actions workflow runs the tests,
writes a JUnit report, and publishes the `cilog` Markdown report in the job summary.

## Development

```bash
ruff check .
ruff format --check .
mypy src tests
pytest            # includes coverage, minimum 95 %
```

## Design choices


## What I learned


## Tech
Python 3.12+, pytest, ruff, mypy, GitHub Actions