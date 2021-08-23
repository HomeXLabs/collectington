"""Module that contains function to create a logger object."""
import logging
from config import config


def setup_logging():
    """Return logger object."""
    log_formatter = logging.Formatter(
        config.BaseConfig.LOG_MSG_FORMAT, config.BaseConfig.LOG_DATE_FORMAT
    )

    logger = logging.getLogger(config.BaseConfig.DATA_COLLECTION_LOGGER)
    logger.setLevel(config.BaseConfig.LOG_LOGGING_LEVEL)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logger.addHandler(console_handler)
    logger.handlers[:] = [console_handler]

    return logger
