"""File to run the API for a service."""
import sys
import time
import traceback

from argparse import ArgumentParser

from prometheus_client import start_http_server

from collectington.config import get_config, get_services
from collectington.logger import setup_logging
from collectington.ascii_art import print_ascii


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


def parse_args():
    """Parse functions passed to program."""
    parser = ArgumentParser(description="Add a service for Prometheus to monitor.")

    parser.add_argument(
        "-s",
        "--service",
        type=str,
        required=True,
        help="Provide the name of a service to be monitored",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="Provide the path of your configuration file",
    )

    args = vars(parser.parse_args())

    return (args["service"], args["config"])


def run(service, metrics_list, metric_instances_list):
    """Try to process an API request."""
    try:
        process_request(service, metrics_list, metric_instances_list)
        time.sleep(config["api_call_intervals"])
    except Exception as err:
        traceback.print_exc()
        logger.error("Error has occurred: %s", err)
        sys.exit(1)


if __name__ == "__main__":

    service_name, config_path = parse_args()

    print_ascii()

    logger = setup_logging()

    logger.info("Reading config from %s", config_path)

    config = get_config(config_path)

    logger.info("Setting up Services")
    services = get_services(config)

    logger.info("Services retrieved: %s", ", ".join(services))

    for s_name, service in services.items():
        logger.info("Generating Prometheus Metric Instances for %s", service)
        service["list_of_metric_instances"] = service[
            "api_service"
        ].generate_prometheus_metric_instances()

    logger.info("Setting up HTTP Server - PORT: %s", config["port"])
    start_http_server(config["port"])

    while True:
        # TODO: replace arguments with dict reference for service defined above
        run(api_service, list_of_metrics, list_of_metric_instances)
