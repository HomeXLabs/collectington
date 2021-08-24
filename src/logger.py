"""Module that contains function to create a logger object."""
import logging

LOG_MSG_FORMAT = "%(asctime)s|%(name)-12s|%(levelname)-8s|%(message)s"
LOG_DATE_FORMAT = "%Y/%m/%d|%H:%M:%S"
LOGGING_LEVEL = "INFO"
DATA_COLLECTION_LOGGER = "DATA-COLLECTION"


def setup_logging():
    """Return logger object."""
    log_formatter = logging.Formatter(LOG_MSG_FORMAT, LOG_DATE_FORMAT)

    logger = logging.getLogger(DATA_COLLECTION_LOGGER)
    logger.setLevel(LOGGING_LEVEL)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logger.addHandler(console_handler)
    logger.handlers[:] = [console_handler]

    return logger
