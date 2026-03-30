"""Structlog configuration.

User-facing output goes to stdout via Rich.
Structured logs go to file. Debug mode sends human-readable logs to stderr.
"""

from __future__ import annotations

import sys
from pathlib import Path

import structlog


def setup_logging(verbose: bool = False) -> None:
    """Configure structlog. Logs go to file; verbose mode adds stderr output."""
    log_dir = Path.home() / ".local" / "share" / "vaultmind"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "vaultmind.log"

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if verbose:
        structlog.configure(
            processors=[
                *processors,
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(0),
            logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        )
    else:
        structlog.configure(
            processors=[
                *processors,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(20),
            logger_factory=structlog.PrintLoggerFactory(file=open(log_file, "a")),  # noqa: SIM115
        )
