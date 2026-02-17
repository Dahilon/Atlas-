import logging
from logging.config import dictConfig


def setup_logging() -> None:
    """
    Configure application-wide structured logging.

    We keep this simple but production-like:
    - INFO-level by default
    - key=value style formatting for easier parsing
    """

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s "
                        "%(levelname)s "
                        "%(name)s "
                        "%(message)s"
                    ),
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"],
            },
        }
    )


logger = logging.getLogger("events-risk-dashboard")

