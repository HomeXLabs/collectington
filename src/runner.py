"""File to run the API for a service."""
import sys
import time
import traceback

from argparse import ArgumentParser

from prometheus_client import start_http_server

from config import config
from src.logger import setup_logging
from src.api_factory import ApiFactory
from src.validator import get_service_cls, validate_service


def process_request(api_service, list_of_metrics, list_of_metric_instances):
    """Receive request for an API service
       Return formatted output of metrics.
    """
    # TODO: multithread the calls
    service_metric_dict = {}

    for metric in list_of_metrics:
        metric_value = api_service.get_metric(metric)

        if metric_value is None:
            metric_value = 0

        service_metric_dict[metric] = metric_value

    api_service.call_prometheus_metrics(service_metric_dict, list_of_metric_instances)


@validate_service()
def get_service(service):
    """Return API factory instance (soon to be deprecated)."""
    api_factory = ApiFactory().get_api_factory(service)
    return api_factory


if __name__ == "__main__":
    parser = ArgumentParser(description="Add a service for Prometheus to monitor.")

    parser.add_argument(
        "-s",
        "--service",
        type=str,
        required=True,
        help="Provide the name of a service to be monitored",
    )

    args = vars(parser.parse_args())
    service_name = args["service"]

    logger = setup_logging()

    logger.info("Setting up Service: %s", service_name)
    api_service = get_service(service_name)

    list_of_metrics = get_service_cls(service_name, config).AVAILABLE_METRICS

    logger.info("Generating Prometheus Metric Instances")
    list_of_metric_instances = api_service.generate_prometheus_metric_instances()

    logger.info("Setting up HTTP Server - PORT: %s", config.BaseConfig.PORT)
    start_http_server(int(config.BaseConfig.PORT))

    while True:
        try:
            process_request(api_service, list_of_metrics, list_of_metric_instances)
            time.sleep(int(config.BaseConfig.API_CALL_INTERVALS))
        except Exception as e:
            traceback.print_exc()
            logger.error("Error has occurred: %s", e)
            sys.exit(1)
