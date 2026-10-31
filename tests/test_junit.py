import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import Status
from ci_log_analyzer.parsers.junit import _parse_suite, _parse_testcase, parse_junit


def test_testcase_passed():
    passed_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name="passed_testcase" time="0.5">'
        "</testcase>"
    )
    result = _parse_testcase(passed_testcase)
    assert result.name == "passed_testcase"
    assert result.classname == "tests.test_fixtures"
    assert result.duration == 0.5
    assert result.status is Status.PASSED
    assert result.message is None


def test_testcase_failed():
    failed_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="failed_testcase" time="1.56">'
        '<failure message="assert 1 == 2"></failure></testcase>'
    )
    result = _parse_testcase(failed_testcase)
    assert result.status is Status.FAILED
    assert result.message == "assert 1 == 2"


def test_testcase_error():
    error_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="error_testcase" time="3.56">'
        '<error message="failed on setup"></error></testcase>'
    )
    result = _parse_testcase(error_testcase)
    assert result.status is Status.ERROR
    assert result.message == "failed on setup"


def test_testcase_skipped():
    skipped_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="skipped_testcase" '
        'time="1.56"><skipped type="pytest.skip" message="Skipping '
        'french test only"></skipped>'
        "</testcase>"
    )
    result = _parse_testcase(skipped_testcase)
    assert result.status is Status.SKIPPED
    assert result.message == "Skipping french test only"


def test_testcase_missing_name():
    missing_name = ET.fromstring(
        '<testcase classname="tests.test_fixtures" time="1.56"></testcase>'
    )
    with pytest.raises(ParseError, match="Name of the TestCase can't be empty"):
        _parse_testcase(missing_name)


def test_testcase_missing_classname():
    missing_classname = ET.fromstring(
        '<testcase name="passed_testcase" time="0.5"></testcase>'
    )
    result = _parse_testcase(missing_classname)
    assert result.classname == ""


def test_testcase_missing_time():
    missing_time = ET.fromstring(
        '<testcase classname="test.test_fixtures" name ="passed_testcase"></testcase>'
    )
    result = _parse_testcase(missing_time)
    assert result.duration == 0.0


def test_testcase_invalid_time():
    invalid_time = ET.fromstring(
        '<testcase classname="test.test_fixtures" name ="passed_testcase" time="abc">'
        "</testcase>"
    )
    with pytest.raises(ParseError, match="abc"):
        _parse_testcase(invalid_time)


def test_testcase_unknown_child():
    unknown_child = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="system_testcase" time="1.56">'
        '<system-out message="System"></system-out></testcase>'
    )
    result = _parse_testcase(unknown_child)
    assert result.message is None
    assert result.status is Status.PASSED


def test_testsuite_missing_name():
    missing_name = ET.fromstring(
        "<testsuite>"
        '<testcase classname="tests.test_fixtures" name="test_pass" time="1.56">'
        "</testcase>"
        "</testsuite>"
    )
    result = _parse_suite(missing_name)
    assert result.name == ""


def test_testsuite_with_name():
    with_name = ET.fromstring(
        '<testsuite name="pytest">'
        '<testcase classname="tests.test_fixtures" name="test_pass" time="1.56">'
        "</testcase>"
        "</testsuite>"
    )
    result = _parse_suite(with_name)
    assert result.name == "pytest"


def test_testsuite_three_testcase():
    test_cases = ET.fromstring(
        "<testsuite>"
        '<testcase classname="tests.test_fixtures" name="test_pass1" time="1.56">'
        "</testcase>"
        '<testcase classname="tests.test_fixtures" name="test_pass2" time="2.34">'
        "</testcase>"
        '<testcase classname="tests.test_fixtures" name="test_pass3" time="0.56">'
        "</testcase>"
        "</testsuite>"
    )
    result = _parse_suite(test_cases)
    assert result.test_cases[0].name == "test_pass1"
    assert result.test_cases[1].name == "test_pass2"
    assert result.test_cases[2].name == "test_pass3"
    assert len(result.test_cases) == 3


def test_testsuite_mixed_statuses():
    test_cases = ET.fromstring(
        "<testsuite>"
        '<testcase classname="tests.test_fixtures" name="test_pass" time="1.56">'
        "</testcase>"
        '<testcase classname="tests.test_fixtures" name ="skipped_testcase" '
        'time="1.56"><skipped type="pytest.skip" message="Skipping '
        'french test only"></skipped>'
        "</testcase>"
        '<testcase classname="tests.test_fixtures" name ="error_testcase" time="3.56">'
        '<error message="failed on setup"></error>'
        "</testcase>"
        '<testcase classname="tests.test_fixtures" name ="failed_testcase" time="1.56">'
        '<failure message="assert 1 == 2"></failure>'
        "</testcase>"
        "</testsuite>"
    )
    result = _parse_suite(test_cases)
    assert result.test_cases[0].status is Status.PASSED
    assert result.test_cases[1].status is Status.SKIPPED
    assert result.test_cases[2].status is Status.ERROR
    assert result.test_cases[3].status is Status.FAILED
    assert len(result.test_cases) == 4


def test_testsuite_not_only_testcase():
    test_cases = ET.fromstring(
        "<testsuite>"
        '<testcase classname="tests.test_fixtures" name="test_pass" time="1.56">'
        "</testcase>"
        '<testcase classname="tests.test_fixtures" name ="skipped_testcase" '
        'time="1.56"><skipped type="pytest.skip" message="Skipping '
        'french test only"></skipped>'
        "</testcase>"
        '<system-out message="System"></system-out>'
        "</testsuite>"
    )
    result = _parse_suite(test_cases)
    assert len(result.test_cases) == 2


def test_testsuite_no_testcase():
    test_cases = ET.fromstring("<testsuite></testsuite>")
    result = _parse_suite(test_cases)
    assert len(result.test_cases) == 0


def test_testsuite_broken_testcase():
    invalid_time = ET.fromstring(
        "<testsuite>"
        '<testcase classname="test.test_fixtures" name ="passed_testcase" time="abc">'
        "</testcase>"
        "</testsuite>"
    )
    with pytest.raises(ParseError, match="abc"):
        _parse_suite(invalid_time)


def test_parse_junit_not_valid_path():
    path = Path(__file__).parent / "fixtures/junit_mixed_false.xml"
    with pytest.raises(ParseError, match="cannot be opened"):
        parse_junit(path)


def test_parse_junit_directory_raise():
    path = Path()
    with pytest.raises(ParseError, match="cannot be opened"):
        parse_junit(path)


def test_parse_junit_valid_path():
    path = Path(__file__).parent / "fixtures/junit_mixed.xml"
    list_test_suite = parse_junit(path)
    assert list_test_suite[0].name == "pytest"
    assert len(list_test_suite[0].test_cases) == 4
    assert list_test_suite[0].test_cases[0].status is Status.PASSED
    assert list_test_suite[0].test_cases[1].status is Status.FAILED
    assert list_test_suite[0].test_cases[2].status is Status.ERROR
    assert list_test_suite[0].test_cases[3].status is Status.SKIPPED
    assert list_test_suite[0].test_cases[2].duration == 0.000


def test_parse_junit_single_testsuite(tmp_path):
    content = (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<testsuite name='pytest' tests='1' time='0.075'>"
        "<testcase classname='tests.test_fixtures' name='test_pass' time='0.001'/>"
        "</testsuite>"
    )
    file = tmp_path / "false_test_suite.xml"
    file.write_text(content, encoding="utf-8")
    test_suite = parse_junit(file)
    assert len(test_suite[0].test_cases) == 1
    assert test_suite[0].name == "pytest"
    assert test_suite[0].test_cases[0].status is Status.PASSED
    assert test_suite[0].test_cases[0].name == "test_pass"
    assert test_suite[0].test_cases[0].duration == 0.001


def test_parse_junit_malformed_xml(tmp_path):
    content = (
        "<?xml version='1.0' encoding='utf-8'?>testsuites name='pytest tests'"
        "<testsuite name='pytest' tests='1' time='0.075'>"
        "<testcase classname='tests.test_fixtures' name='test_pass' time='0.001'/>"
        "</testsuite></testsuites>"
    )
    file = tmp_path / "false_test_suite.xml"
    file.write_text(content, encoding="utf-8")

    with pytest.raises(ParseError, match="cannot be parsed"):
        parse_junit(file)


def test_parse_junit_no_testsuite(tmp_path):
    content = "<?xml version='1.0' encoding='utf-8'?><html/>"
    file = tmp_path / "false_test_suite.xml"
    file.write_text(content, encoding="utf-8")

    with pytest.raises(ParseError, match="Not a JUnit file"):
        parse_junit(file)
