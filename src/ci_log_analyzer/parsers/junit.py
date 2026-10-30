import xml.etree.ElementTree as ET

from ci_log_analyzer.errors import ParseError
from ci_log_analyzer.models import Status, TestCase

# def parse_junit(path: Path) -> list[TestSuiteResult]:


# def _parse_suite(element) -> TestSuiteResult:


TAG_TO_STATUS = {
    "failure": Status.FAILED,
    "error": Status.ERROR,
    "skipped": Status.SKIPPED,
}


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
            "converted to float type."
        ) from err

    test_case = TestCase(
        case_name, case_classname, case_status, case_duration, case_message
    )
    return test_case
