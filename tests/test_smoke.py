import ci_log_analyzer


def test_name():
    name = ci_log_analyzer.__name__
    assert name == "ci_log_analyzer"
