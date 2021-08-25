"""File to run the API for a service."""
import sys
import time
import traceback

from argparse import ArgumentParser

from prometheus_client import start_http_server

from collectington.config import (
        get_config,
        get_service,
        get_list_of_available_metrics
        )
from collectington.logger import setup_logging


def process_request(service, metrics_list, metric_instances_list):
    """Receive request for an API service
    Return formatted output of metrics.
    """
    service_metric_dict = {}

    for metric in metrics_list:
        metric_value = service.get_metric(metric)

        if metric_value is None:
            metric_value = 0

        service_metric_dict[metric] = metric_value

    service.call_prometheus_metrics(service_metric_dict, metric_instances_list)


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

    config_path = "config/config.json"
    logger.info("Reading config from %s", config_path)

    config = get_config(config_path)

    logger.info("Setting up Service: %s", service_name)
    api_service = get_service(config, service_name)

    list_of_metrics = get_list_of_available_metrics(config, service_name)

    logger.info("Generating Prometheus Metric Instances")
    list_of_metric_instances = api_service.generate_prometheus_metric_instances()

    logger.info("Setting up HTTP Server - PORT: %s", config["port"])
    start_http_server(config["port"])

    while True:
        try:
            process_request(api_service, list_of_metrics, list_of_metric_instances)
            time.sleep(config["api_call_intervals"])
        except Exception as e:
            traceback.print_exc()
            logger.error("Error has occurred: %s", e)
            sys.exit(1)
