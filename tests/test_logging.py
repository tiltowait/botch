import io
import logging
import re
import sys

import pytest

import logconfig


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    sys.stdout, sys.stderr = stdout, stderr

    # Configure logging
    logconfig.configure_logging()
    logger = logging.getLogger(__name__)

    yield logger, stdout, stderr

    # Teardown: Reset stdout and stderr
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__


def test_info_to_stdout(setup_and_teardown):
    logger, stdout, stderr = setup_and_teardown
    logger.info("Test info message")
    assert "Test info message" in stdout.getvalue()
    assert "Test info message" not in stderr.getvalue()


def test_warning_to_stderr(setup_and_teardown):
    logger, stdout, stderr = setup_and_teardown
    logger.warning("Test warning message")
    assert "Test warning message" in stderr.getvalue()
    assert "Test warning message" not in stdout.getvalue()


def test_error_to_stderr(setup_and_teardown):
    logger, stdout, stderr = setup_and_teardown
    logger.error("Test error message")
    assert "Test error message" in stderr.getvalue()
    assert "Test error message" not in stdout.getvalue()


def test_critical_to_stderr(setup_and_teardown):
    logger, stdout, stderr = setup_and_teardown
    logger.critical("Test critical message")
    assert "Test critical message" in stderr.getvalue()
    assert "Test critical message" not in stdout.getvalue()


def test_debug_not_logged(setup_and_teardown):
    logger, stdout, stderr = setup_and_teardown
    logger.debug("Test debug message")
    assert "Test debug message" not in stdout.getvalue()
    assert "Test debug message" not in stderr.getvalue()


def test_log_format(setup_and_teardown):
    logger, stdout, _ = setup_and_teardown
    logger.info("Test format")
    log_output = stdout.getvalue().strip()
    expected_pattern = r"INFO     \| \S+(\s+\S+)* \| Test format"
    match = re.match(expected_pattern, log_output)
    assert match is not None


def test_log_level_padding(setup_and_teardown):
    logger, stdout, stderr = setup_and_teardown
    logger.info("Info")
    logger.warning("Warning")
    stdout_output = stdout.getvalue()
    stderr_output = stderr.getvalue()
    assert "INFO     |" in stdout_output
    assert "WARNING  |" in stderr_output


def test_logger_name_padding(setup_and_teardown):
    _, stdout, _ = setup_and_teardown

    # Test short logger name
    custom_logger = logging.getLogger("test")
    custom_logger.info("Test logger name")
    log_output = stdout.getvalue()
    assert re.search(r"\| test       \|", log_output) is not None

    # Clear the stdout buffer
    stdout.truncate(0)
    stdout.seek(0)

    # Test long logger name
    long_name_logger = logging.getLogger("very_long_name")
    long_name_logger.info("Test long logger name")
    log_output = stdout.getvalue()
    assert re.search(r"\| very_long_name \|", log_output) is not None
