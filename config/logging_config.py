
"""
Logging configuration for AtmoSync.
"""

import logging
import logging.config

from config.settings import LOG_LEVEL


def setup_logging():
    """
    Configure application-wide logging.
    """

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,

            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s | "
                        "%(levelname)s | "
                        "%(name)s | "
                        "%(message)s"
                    )
                }
            },

            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": LOG_LEVEL,
                    "formatter": "standard",
                }
            },

            "root": {
                "level": LOG_LEVEL,
                "handlers": ["console"],
            },
        }
    )


def get_logger(name):
    """
    Return a logger for the requested module.
    """

    return logging.getLogger(name)
