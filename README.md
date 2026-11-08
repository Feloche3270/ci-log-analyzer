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

### Grouping errors

Build logs often repeat the same error with small differences, such as a duration,
a job ID or a file path. To count how often each kind of error occurs, error and
failure messages are normalised before grouping: timestamps, paths and numbers are
replaced with placeholders (`<TIMESTAMP>`, `<PATH>`, `<N>`).

    Timeout after 12 s in /app/tests/test_smoke.py (job 50991)
    Timeout after 4 s in /app/tests/test_junit.py (job 50996)
    → Timeout after <N> s in <PATH> (job <N>)

Each group keeps its normalised pattern, its count and **the line numbers of all
its occurrences**. Normalising answers "how often does this happen?", while the
line numbers answer "where do I look to fix it?".

I considered showing a single real message as an example, but the first occurrence
is not always representative: if one error mentions `test_smoke.py` and fourteen
others mention `test_junit.py`, the example would point to the wrong place. Keeping
every line number is complete and unbiased, and costs only one list per group.

### Parsers store facts, reports decide presentation

The parsers keep data as raw as possible: log messages are stored exactly as they
appear, and normalisation happens only when errors are grouped. The analysis
returns plain values (for example, the pass rate is `0.25`, or `None` when no test
ran), and each report formats them for its readers: `25.00%` and `n/a` in the
terminal and Markdown reports, the raw number and `null` in JSON. Report functions
return strings; the CLI decides whether to print them or write them to a file,
which also makes every report testable with a plain comparison.

### Missing and unexpected data

The rule is to ignore what the tool does not need, and to fail clearly on what it
cannot use. Valid JUnit elements such as `<system-out>` or `<properties>` are
skipped, and log lines without a level are ignored. A test case without a name, an
invalid duration, malformed XML or an unknown root element raise an error, because
the result would be unreliable. Optional attributes get neutral defaults: a missing
duration becomes `0.0`, so sums and the slowest-tests ranking stay correct, and a
missing class name or suite name becomes an empty string.

### Exit codes

The tool's job is to report, so by default it exits with `0` whenever the report was
produced, even if tests failed. Failing a pipeline is a separate decision that the
user makes with `--fail-on-failures`, which returns `1` when a test failed or errored.
Errors found in build logs never change the exit code: they are information for the
report. Invalid arguments and unreadable files return `2`.

### Errors

Both parsers raise a single `ParseError`, defined in its own module, with a message
that names the file and the problem. The original exception is kept as its cause.
Only the CLI catches it: it prints the message on `stderr` and exits with code `2`.

## Known limitations

- Normalisation can group messages that differ by a meaningful number, for example
  `exit code 1` and `exit code 137`.
- Any word containing a `/` or `\` is treated as a path, so `and/or` becomes `<PATH>`.
- A logger prefix is kept in the message: `ERROR:root:Connection lost` and
  `ERROR Connection lost` are grouped separately.
- Build logs must be UTF-8. UTF-16 files are rejected with a clear error.
- JUnit reports are detected by their `.xml` extension; a report saved under another
  name is read as a text log.
- A missing test duration cannot be told apart from a test that took 0 s.

## What I learned

- **Regular expressions.** Detecting log levels and normalising messages taught me
  word boundaries (`\bERROR\b` must not match `test_error_handling`), capturing
  versus non-capturing groups, and why the order of replacements matters:
  replacing numbers first would destroy timestamps and paths before their own
  patterns could match them.

- **Writing tests that can actually fail.** Early on, I sometimes copied expected
  values from my code's output, or checked that a field was `not None`, which
  proves almost nothing. I learned to write expected values from the input, to
  compare whole objects, to test error paths with `pytest.raises`, and to use
  golden files for exact text output. One test once compared a hard-coded list
  with itself and could never fail.

- **Cross-platform issues.** Several bugs only appeared because I develop on
  Windows and CI runs on Linux: PowerShell writing a fixture in
  UTF-16, and opening a directory raising `PermissionError` on Windows but
  `IsADirectoryError` on Linux. Catching the common parent `OSError`, and testing
  with `tmp_path` instead of the current folder, made the behaviour the same
  everywhere.

- **CI is about checking results, not just green steps.** My first job-summary step
  was green but wrote the report to the wrong file, because of a misplaced `$`. I
  also broke a test on purpose to confirm that the pipeline really fails, and
  protected `main` so it only changes through pull requests with passing checks.

- **Separating responsibilities.** Keeping parsing, analysis and presentation in
  separate modules, with reports returning strings, made each part easy to test on
  its own, and let me add a JSON report almost for free.


## Tech
Python 3.12+, pytest, ruff, mypy, GitHub Actions