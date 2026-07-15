import logging
import sys

from app.core.config import settings


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, 'request_id', '-')
        return True


def setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s  [req=%(request_id)s]",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("minio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
