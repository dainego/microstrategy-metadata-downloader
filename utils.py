import logging
from pathlib import Path


def setup_logger(
    name: str,
    log_file: Path | str,
    level: int = logging.INFO
) -> logging.Logger:

    """
    Creates a logger that writes messages to both the console
    and a log file.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if the logger is initialized again
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Log to File
    if log_file:
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def clean_text(value: str | None) -> str | None:
    """
    Removes line breaks, tabs, and repeated whitespace from text.
    """

    if value is None:
        return None

    return " ".join(value.split())


