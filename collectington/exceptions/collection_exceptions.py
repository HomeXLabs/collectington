"""A module to define exceptions that could occur during web scraping."""


class InvalidServiceTypeException(Exception):
    """Service type is not considered valid."""


class InvalidMetricTypeException(Exception):
    """Metric type is not considered valid."""


class UndefinedMetricException(Exception):
    """Metric being used has not been defined."""


class UnsupportedPrometheusInstance(Exception):
    """The prometheus instance being used in not supported."""
