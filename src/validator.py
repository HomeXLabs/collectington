import sys
import inspect

from functools import wraps

import configs.config as config
from exceptions.collection_exceptions import (
    InvalidServiceTypeException,
    InvalidMetricTypeException,
)


def get_valid_services():
    list_of_clsmembers = inspect.getmembers(config, inspect.isclass)
    list_of_clsmembers = [
        cls[0].replace("Config", "").lower() for cls in list_of_clsmembers
    ]
    list_of_clsmembers.remove("base")
    return list_of_clsmembers


def get_service_cls(service, config):
    clsname = "{}{}".format(str(service).title(), "Config")

    list_of_clsmembers = inspect.getmembers(config, inspect.isclass)
    cls_obj = [cls[1] for cls in list_of_clsmembers if clsname == cls[0]][0]

    return cls_obj


def is_valid_service_type(service):
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
