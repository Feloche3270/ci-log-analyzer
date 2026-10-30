import xml.etree.ElementTree as ET

import pytest

from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import Status
from ci_log_analyzer.parsers.junit import _parse_testcase


def test_passed():
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


def test_failed():
    failed_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="failed_testcase" time="1.56">'
        '<failure message="assert 1 == 2"></failure></testcase>'
    )
    result = _parse_testcase(failed_testcase)
    assert result.status is Status.FAILED
    assert result.message == "assert 1 == 2"


def test_error():
    error_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="error_testcase" time="3.56">'
        '<error message="failed on setup"></error></testcase>'
    )
    result = _parse_testcase(error_testcase)
    assert result.status is Status.ERROR
    assert result.message == "failed on setup"


def test_skipped():
    skipped_testcase = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="skipped_testcase" '
        'time="1.56"><skipped type="pytest.skip" message="Skipping '
        'french test only"></skipped>'
        "</testcase>"
    )
    result = _parse_testcase(skipped_testcase)
    assert result.status is Status.SKIPPED
    assert result.message == "Skipping french test only"


def test_missing_name():
    missing_name = ET.fromstring(
        '<testcase classname="tests.test_fixtures" time="1.56"></testcase>'
    )
    with pytest.raises(ParseError, match="Name of the TestCase can't be empty"):
        _parse_testcase(missing_name)


def test_missing_classname():
    missing_classname = ET.fromstring(
        '<testcase name="passed_testcase" time="0.5"></testcase>'
    )
    result = _parse_testcase(missing_classname)
    assert result.classname == ""


def test_missing_time():
    missing_time = ET.fromstring(
        '<testcase classname="test.test_fixtures" name ="passed_testcase"></testcase>'
    )
    result = _parse_testcase(missing_time)
    assert result.duration == 0.0


def test_invalid_time():
    invalid_time = ET.fromstring(
        '<testcase classname="test.test_fixtures" name ="passed_testcase" time="abc">'
        "</testcase>"
    )
    with pytest.raises(ParseError, match="abc"):
        _parse_testcase(invalid_time)


def test_unknown_child():
    unknown_child = ET.fromstring(
        '<testcase classname="tests.test_fixtures" name ="system_testcase" time="1.56">'
        '<system-out message="System"></system-out></testcase>'
    )
    result = _parse_testcase(unknown_child)
    assert result.message is None
    assert result.status is Status.PASSED
