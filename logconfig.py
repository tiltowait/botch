"""This module configures the logger to only output actual problems to stderr.
This fixes an issue where Railway reports every log statement as an error and
makes filtering and analysis difficult."""

import logging
import sys


class InfoFilter(logging.Filter):
    """A custom logging filter that only allows log records with level INFO or lower."""

    def filter(self, record):
        """Filter log records based on their level.

        Args:
            record (logging.LogRecord): The log record to be filtered.

        Returns:
            bool: True if the record's level is INFO or lower, False otherwise."""
        return record.levelno <= logging.INFO


def configure_logging():
    """Configure the root logger with custom handlers for stdout and stderr.

    This function sets up the root logger to output INFO and DEBUG messages to stdout,
    and WARNING, ERROR, and CRITICAL messages to stderr. It uses a custom formatter
    and applies the InfoFilter to the stdout handler."""
    root_logger = logging.getLogger()

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # Configure stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(InfoFilter())
    stdout_handler.setLevel(logging.INFO)

    # Configure stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)

    # Set up formatter
    formatter = logging.Formatter("%(levelname)-8s | %(name)-10s | %(message)s")
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)
