import inspect

from functools import wraps

import config.config as config
from exceptions.collection_exceptions import (
    InvalidServiceTypeException,
    InvalidMetricTypeException,
)


def get_valid_services():
    """Return a list of valid services defined in config."""
    list_of_clsmembers = inspect.getmembers(config, inspect.isclass)
    list_of_clsmembers = [
        cls[0].replace("Config", "").lower() for cls in list_of_clsmembers
    ]
    list_of_clsmembers.remove("base")
    return list_of_clsmembers


def get_service_cls(service, external_config):
    clsname = "{}{}".format(str(service).title(), "Config")

    list_of_clsmembers = inspect.getmembers(external_config, inspect.isclass)
    cls_obj = next(cls[1] for cls in list_of_clsmembers if cls[0] == clsname)

    return cls_obj


def is_valid_service_type(service):
    """Check that service is of a type defined in the config."""
    list_of_valid_services = get_valid_services()
    return service in list_of_valid_services


def validate_service():
    """
    This function is a decorator to validate service defined from config.py
    All valid services are expected to have its own class defined from config.py

    This func will call is_valid_service_type which validates the name of each service.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_valid_service_type(args[0]):
                raise InvalidServiceTypeException

            return func(*args, **kwargs)

        return wrapper

    return decorator
