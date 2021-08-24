"""Module for parsing and validating config files."""
import sys
import itertools

from json.decoder import (
        JSONDecoder,
        JSONDecodeError
        )

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



def get_list_of_available_metrics():
    """
    Get all the available metrics from a config file
    and merge it into a single list.
    """
    config = read_config("./config/config.json")

    metrics_mapping = config["services"][0]["prometheus_metrics_mapping"]
    list_of_available_metrics = [v for k,v in metrics_mapping.items()]
    list_of_available_metrics = list(itertools.chain(*list_of_available_metrics))

    return list_of_available_metrics
