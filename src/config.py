"""Module for parsing and validating config files."""
import sys
import itertools
import importlib

from json.decoder import JSONDecoder, JSONDecodeError

from src.logger import setup_logging

DECODER = JSONDecoder()
LOGGER = setup_logging()


def get_config(path):
    """Read config from a file, parse it, and validate it."""
    with open(path, encoding="utf-8") as file:
        contents = file.read()

    config = parse(contents)

    validate(config)  # ValueError will be raised if there is an issue with the config

    return config


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
    config = read_config(CONFIG_FILE_PATH)

    try:
        for i in range(len(config["services"])):
            if config["services"][i]["service_name"] == service_name:
                return config["services"][i]
    except Exception as err:
        LOGGER.error("Failed to load service config: %s", err)


def get_list_of_available_metrics(service_name):
    """
    Get all the available metrics from a config file
    and merge it into a single list.
    """
    try:
        metrics_mapping = get_service_config(service_name)["prometheus_metrics_mapping"]
        list_of_available_metrics = [v for k, v in metrics_mapping.items()]
        list_of_available_metrics = list(itertools.chain(*list_of_available_metrics))

        return list_of_available_metrics
    except Exception as err:
        LOGGER.error("No available metrics defined in config: %s", err)


def get_service(service_name):
    """Get service class instance using config"""
    try:
        service = get_service_config(service_name)["service_class"]
        service_module = get_service_config(service_name)["service_module"]
        importlib.import_module(service_module)

        return getattr(sys.modules[service_module], service)()
    except Exception as err:
        LOGGER.error("Failed to get service class instance: %s", err)


def get_api_call_intervals():
    config = read_config(CONFIG_FILE_PATH)
    return config["api_call_intervals"]


def get_port_config():
    config = read_config(CONFIG_FILE_PATH)
    return config["port"]


def validate(config):
    """Test that provided json is a valid config."""
    if list(config.keys()) != [
        "port",
        "api_call_intervals",
        "log_level",
        "services",
    ]:
        raise ValueError(
            "Invalid config: config should contain port, api_call_intervals, log_level, services"
        )

    if not isinstance(config["port"], int):
        raise ValueError("Invalid config: port should be an integer")

    if not isinstance(config["api_call_intervals"], int):
        raise ValueError("Invalid config: api_call_intervals should be an integer")

    valid_log_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
    if config["log_level"] not in valid_log_levels:
        raise ValueError(
            f"Invalid config log_lebel must be one of {', '.join(valid_log_levels)}"
        )

    if not isinstance(config["services"], list):
        raise ValueError("Invalid config: services must be a list of services")

    if len(config["services"]) == 0:
        raise ValueError("Invalid config: must contain at least one service")

    validate_services(config["services"])


def validate_services(services):
    """Test that each service in the config is a valid service configuration."""
    for service in services:
        validate_service(service)


def validate_service(service):
    """Test that a service contains a valid configuration."""
    expected_keys = [
        "serviceName",
        "serviceClass",
        "api_url",
        "prometheus_metrics_mapping",
        "secret_file_path",
    ]

    if list(service.keys()) != expected_keys:
        raise ValueError(
            f"Invalid config: all services should contain '{', '.join(expected_keys)}'"
        )

    strings = ["serviceName", "serviceClass", "api_url", "secret_file_path"]

    for field in strings:
        if not isinstance(service[field], str):
            raise ValueError(f"Invalid config: {field} fields should be a string")

    validate_metrics_mapping(
        service["serviceName"], service["prometheus_metrics_mapping"]
    )


def validate_metrics_mapping(service_name, metrics_mapping):
    """Test that the metrics mapping of a service is valid."""
    valid_metric_types = ["counter", "summary"]

    if not isinstance(metrics_mapping, dict):
        raise ValueError(
            f"Invalid config: {service_name} prometheus_metrics_mapping should be a dict"
        )

    if len(set(metrics_mapping)) != len(metrics_mapping):
        raise ValueError(
            f"Invalid config: {service_name} prometheus_metrics_mapping\
should contain only one of each metric type"
        )

    if not all(metric_type in valid_metric_types for metric_type in metrics_mapping):
        raise ValueError(
            f"Invalid config: {service_name} prometheus_metrics_mapping\
can only be one of {', '.join(valid_metric_types)}"
        )

    metrics = []

    for metric_type in metrics_mapping:
        metrics = metrics + metrics_mapping[metric_type]

    for metric in metrics:
        if not isinstance(metric, str):
            raise ValueError(
                f"Invalid config: {service_name} metric '{metric}' is not a string"
            )
