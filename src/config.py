"""Module for parsing and validating config files."""
import sys
import itertools
import importlib

from json.decoder import JSONDecoder, JSONDecodeError

from src.logger import setup_logging

DECODER = JSONDecoder()
LOGGER = setup_logging()


def parse(config):
    """Parse the string of a config file."""
    try:
        output = DECODER.decode(config)
    except JSONDecodeError as err:
        LOGGER.error("Failed to parse config file: %s", err)
        raise
    except TypeError as err:
        LOGGER.error("Failed to parse config file: %s", err)
        raise

    return output


def read_config(config_file_path):
    with open(config_file_path) as f:
        config = f.read()

        parsed_config = parse(config)
    return parsed_config


def get_service_config(service_name):
    config = read_config("./config/config.json")

    for i in range(len(config["services"])):
        if config["services"][i]["service_name"] == service_name:
            return config["services"][i]


def get_list_of_available_metrics(service_name):
    """
    Get all the available metrics from a config file
    and merge it into a single list.
    """

    metrics_mapping = get_service_config(service_name)["prometheus_metrics_mapping"]
    list_of_available_metrics = [v for k, v in metrics_mapping.items()]
    list_of_available_metrics = list(itertools.chain(*list_of_available_metrics))

    return list_of_available_metrics


def get_service(service_name):
    """Get service class instance using config"""
    service = get_service_config(service_name)["service_class"]
    service_module = get_service_config(service_name)["service_module"]

    importlib.import_module(service_module)

    return getattr(sys.modules[service_module], service)()


def get_api_call_intervals():
    config = read_config("./config/config.json")
    return config["api_call_intervals"]


def get_port_config():
    config = read_config("./config/config.json")
    return config["port"]
