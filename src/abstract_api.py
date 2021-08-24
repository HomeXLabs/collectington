"""Module to define what an API class should do and what it should look like."""
from datetime import datetime

from abc import ABC

import requests

from prometheus_client import Summary, Counter, Gauge, Histogram
from exceptions.collection_exceptions import UnsupportedPrometheusInstance


def enable_delta_metric(func):
    """
    This is a decorator that is used by metric methods. Since each method continuously
    adds total value to Prometheus counter, we do not want to double count metric value
    every time we get API data.

    This will keep track of previous metric and compare against new data to get delta value.
    Previous metric is defined as class attribute for each metric.

    This decorator simply returns the difference between new metric data and previous
    metric data.

    :return: delta of new metric data & previous data
    """

    def wrapper(self):
        # Assigning this to a new variable does not work as this variable will
        # reset value to 0. self is required as this will be called from a class

        previous_metric_name = f"previous_{func.__name__}"

        previous_metric_value = self.__class__._delta_metric_registry[
            previous_metric_name
        ]

        if previous_metric_value == func(self):
            return 0

        delta_metric = func(self) - previous_metric_value

        delta_metric_registry_copy = self.__class__._delta_metric_registry.copy()

        delta_metric_registry_copy[previous_metric_name] = func(self)

        setattr(self.__class__, "_delta_metric_registry", delta_metric_registry_copy)

        return delta_metric

    return wrapper


def register_metric_class(cls):
    """
    This is a class decorator to register metric function with a metric defined in config.
    This removes the process of defining  "get_metric" method like below:

        def get_metric(self, metric):
            if metric == "total_calls"
                return get_total_calls()
            elif metric == "total_missed"
                return get_total_missed()
            else:
                return

    Instead, service class methods that uses register_metric decorator will be auto-registered to
    metric_registry and will be mapped to the correct metric function.

    All subclasses of the AbstractApi class must use this decorator to successfully register all
    metric functions defined in its class.

    """
    cls._metric_registry = {}
    cls._delta_metric_registry = {}

    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method, "_property"):
            cls._metric_registry.update({method._property[0]: methodname})
            cls._delta_metric_registry.update(
                {f"previous_{methodname}": 0}
            )  # this is for delta metric
    return cls


def register_metric(*args):
    """
    This is a class method decorator that registers a method to the registry.

    The argument is the name of a metric defined in config and this name will be mapped to
    the function using the decorator.
    """

    def wrapper(func):
        func._property = args

        return func

    return wrapper


class AbstractApi(ABC):
    """
    This class is an abstract class that includes implementations for common methods
    and forces its subclasses to implement abstract methods.

    The common methods include:
        - reading data via calling an api and cacheing the results
        - Invalidating cache after expiration period
        - Creating Prometheus instances based on config

    Any method can be overridden by its subclasses should a custom method is required.
    """

    def __init__(self):
        self.data_store = {}
        # Prometheus reads data 1 per minute(60 sec)
        self.data_store_expiration_sec = 60

        self.config = None
        self.headers = {}
        self.params = {}
        self.name_of_datastore = ""
        self.api_url = ""

        self.prometheus_metrics_mapping = {
            "counter": Counter,
            "gauge": Gauge,
            "histogram": Histogram,
            "summary": Summary,
        }

    def read_data(self, url, params, headers):
        """Request data from API.
        Update current read time.
        Return API response.
        """
        response = requests.request("GET", url, params=params, headers=headers)
        response = response.json()

        # this is required for invalidating cache after expiry
        self.data_store["data_read_at"] = datetime.now()

        return response

    def is_data_store_expired(self):
        """Check to see if data store has expired.
        Returns boolean.
        """
        data_cached_time = self.data_store["data_read_at"]

        time_delta = datetime.now() - data_cached_time

        return time_delta.total_seconds() >= self.data_store_expiration_sec

    def get_data_from_store(self, name_of_datastore):
        """
        Instead of having to call an API for every metric, different meteics can
        share the same response data(cache) before expiry.
        """
        if not self.data_store.get(name_of_datastore) or self.is_data_store_expired():
            response = self.read_data(self.api_url, self.params, self.headers)

            self.data_store[name_of_datastore] = response

        return self.data_store[name_of_datastore]

    def _init_p_method(self, p_method, api_metric):
        """Internal method to metric methods with labels only if they're provided."""
        if (
            self.config.get("prometheus_metric_labels") is not None
            and api_metric in self.config["prometheus_metric_labels"]
        ):
            labels = self.config["prometheus_metric_labels"][api_metric]
            return p_method(api_metric, api_metric, labels)

        return p_method(api_metric, api_metric)

    def generate_prometheus_metric_instances(self):
        """Create a list of metrics for service."""
        list_of_metric_instances = []

        for p_metric, api_metrics in self.config["prometheus_metrics_mapping"].items():
            p_method = self.prometheus_metrics_mapping[p_metric]

            p_instances = [
                self._init_p_method(p_method, api_metric) for api_metric in api_metrics
            ]

            list_of_metric_instances += p_instances

        return list_of_metric_instances

    def call_prometheus_metrics(self, service_metric_dict, list_of_metric_instances):
        """Handles sending the metric data to prometheus.

        For metrics that have labeled data, we loop through all the labels and
        send each one sequentially.

        For metrics with no label data, we make a single upload for the value.
        """
        for p_instance in list_of_metric_instances:
            metric = str(p_instance).split(":")[1]

            if (
                self.config.get("prometheus_metric_labels") is not None
                and metric in self.config["prometheus_metric_labels"]
            ):
                for labels_and_metric_object in service_metric_dict[metric]:
                    label_list = self.config["prometheus_metric_labels"][metric]
                    labels, val = self._split_labeled_metric_dict(
                        labels_and_metric_object, label_list
                    )
                    self._update_metric(p_instance.labels(*labels), val)
            else:
                self._update_metric(p_instance, service_metric_dict[metric])

    @staticmethod
    def _split_labeled_metric_dict(labeled_metric_dict, label_list):
        """Split single dict into list of labels and the metric value."""
        labeled_metric = labeled_metric_dict.copy()

        labels = []
        for key in label_list:
            labels.append(labeled_metric[key])
            labeled_metric.pop(key, None)

        val = list(labeled_metric.values())[0]

        return labels, val

    @staticmethod
    def _update_metric(p_instance, val):
        """
        Prometheus client includes 4 metrics: Counter, Gauge, Histogram and Summary.
        Each metric needs to be instantiated and each metric calls a method that generates
        outputs in a format that Prometheus can read.

        Example methods include: inc(), dec(), set(), observe() and etc - check documentation

        User of this class can override this method to determine which Prometheus method
        will be used for each metric
        """
        if isinstance(p_instance, Counter):
            # inc is a method from Prometheus client
            p_instance.inc(val)
        elif isinstance(p_instance, (Summary, Histogram)):
            p_instance.observe(val)
        elif isinstance(p_instance, Gauge):
            p_instance.set(val)
        else:
            raise UnsupportedPrometheusInstance

    def get_metric(self, metric):
        """
        This method takes an argument which is a metric name defined in config and will
        key in the value to metric_registry dictionary to get the correct metric function.
        """

        try:
            metric = self.__class__._metric_registry[metric]
            metric_func = getattr(self.__class__, metric)
            return metric_func(self)
        except (IndexError, KeyError):
            # Certain errors occur due to issues with API calls.
            return None
