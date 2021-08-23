import os

from src.utils import get_credentials_from_secret_file


class BaseConfig:
    PORT = os.environ.get("PORT")
    API_CALL_INTERVALS = os.environ.get("API_CALL_INTERVALS")  # seconds
    LOG_MSG_FORMAT = "%(asctime)s|%(name)-12s|%(levelname)-8s|%(message)s"
    LOG_DATE_FORMAT = "%Y/%m/%d|%H:%M:%S"
    LOG_LOGGING_LEVEL = "INFO"
    DATA_COLLECTION_LOGGER = "DATA-COLLECTION"

class SplunkConfig(BaseConfig):
    API_URL = "https://api.victorops.com/api-reporting/v2/incidents"

    AVAILABLE_METRICS = [
        "number_of_incidents",
        "time_taken_to_acknowledge",
        "time_taken_to_resolve",
    ]

    PROMETHEUS_METRICS_MAPPING = {
        "counter": ["number_of_incidents"],
        "summary": ["time_taken_to_acknowledge", "time_taken_to_resolve"],
    }

    dict_of_credentials = get_credentials_from_secret_file(
        os.environ.get("SPLUNK_API_SECRET_FILE_PATH")
    )

    API_ID = dict_of_credentials.get("API_ID", "")
    API_KEY = dict_of_credentials.get("API_KEY", "")
