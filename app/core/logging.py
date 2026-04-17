"""
Centralized logging setup.

One sink to stderr. JSON when LOG_FORMAT=json, otherwise a compact human format.
A `request_id` context var is bound per HTTP request by the middleware; any
log record emitted during the request automatically carries it.
"""
import logging
import os
import sys
from contextvars import ContextVar

from loguru import logger

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def _patch_record(record: dict) -> None:
    record["extra"].setdefault("request_id", request_id_ctx.get())


class _InterceptHandler(logging.Handler):
    """Route stdlib logging (uvicorn, sqlalchemy, httpx, etc.) through loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging() -> None:
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger.remove()
    logger.configure(patcher=_patch_record)

    if log_format == "json":
        logger.add(sys.stderr, level=log_level, serialize=True, backtrace=False, diagnose=False)
    else:
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "<level>{level: <7}</level> "
            "<cyan>{extra[request_id]}</cyan> "
            "<level>{message}</level>"
        )
        logger.add(sys.stderr, level=log_level, format=fmt, backtrace=False, diagnose=False)

    logging.root.handlers = [_InterceptHandler()]
    logging.root.setLevel(log_level)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "sqlalchemy.engine", "httpx"):
        std = logging.getLogger(name)
        std.handlers = [_InterceptHandler()]
        std.propagate = False
