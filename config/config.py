import os

from src.utils import get_credentials_from_secret_file


class BaseConfig:
    PORT = os.environ.get("PORT")
    API_CALL_INTERVALS = os.environ.get("API_CALL_INTERVALS")  # seconds
    LOG_MSG_FORMAT = "%(asctime)s|%(name)-12s|%(levelname)-8s|%(message)s"
    LOG_DATE_FORMAT = "%Y/%m/%d|%H:%M:%S"
    LOG_LOGGING_LEVEL = "INFO"
    DATA_COLLECTION_LOGGER = "DATA-COLLECTION"