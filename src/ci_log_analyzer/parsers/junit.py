import xml.etree.ElementTree as ET
from pathlib import Path

from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import Status, TestCase, TestSuiteResult

TAG_TO_STATUS = {
    "failure": Status.FAILED,
    "error": Status.ERROR,
    "skipped": Status.SKIPPED,
}


def parse_junit(path: Path) -> list[TestSuiteResult]:
    try:
        tree = ET.parse(path)
    except ET.ParseError as err:
        raise ParseError(f"File {path} cannot be parsed") from err
    except OSError as err:
        raise ParseError(f"File {path} cannot be opened") from err

    root = tree.getroot()

    if root.tag == "testsuites":
        return [_parse_suite(test_suite) for test_suite in root.findall("testsuite")]
    elif root.tag == "testsuite":
        return [_parse_suite(root)]
    else:
        raise ParseError(f"Not a JUnit file: {root.tag}")


def _parse_suite(element: ET.Element) -> TestSuiteResult:
    suite_name = element.get("name", "")
    test_cases = [
        _parse_testcase(test_case) for test_case in element.findall("testcase")
    ]
    return TestSuiteResult(suite_name, test_cases)


def _parse_testcase(element: ET.Element) -> TestCase:
    case_name = element.get("name")
    if not case_name:
        raise ParseError("Name of the TestCase can't be empty")

    case_classname = element.get("classname", "")
    case_status = Status.PASSED
    case_message = None
    for child in element:
        if child.tag in TAG_TO_STATUS:
            case_status = TAG_TO_STATUS[child.tag]
            case_message = child.get("message")

    try:
        case_duration = float(element.get("time", "0.0"))
    except ValueError as err:
        raise ParseError(
            f"Invalid time: '{element.get('time')}' in test case {case_name} cannot be"
            " converted to float type."
        ) from err

    return TestCase(case_name, case_classname, case_status, case_duration, case_message)
