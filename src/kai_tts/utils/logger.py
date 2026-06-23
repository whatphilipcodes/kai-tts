import logging

from src.kai_tts.config import settings


def setup_logging() -> None:
    """
    Initialize and configure the logging system.
    """

    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(fmt)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.system.log_level)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(settings.system.log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for h in root_logger.handlers:
            h.setLevel(settings.system.log_level)
            h.setFormatter(formatter)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)