import logging

from backend.core.compliance import redact_sensitive


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive(record.msg)
        if record.args:
            record.args = redact_sensitive(record.args)
        return True


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    sensitive_filter = SensitiveDataFilter()
    root = logging.getLogger()
    root.addFilter(sensitive_filter)
    for handler in root.handlers:
        handler.addFilter(sensitive_filter)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
