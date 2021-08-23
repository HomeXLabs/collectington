import os
import requests
import datetime
import statistics

from prometheus_client import Summary, Counter, Gauge, Histogram

from src.utils import *
from config.config import *
from src.abstract_api import (
    AbstractApi,
    enable_delta_metric,
    register_metric_class,
    register_metric,
)
from exceptions.collection_exceptions import UndefinedMetricException


@register_metric_class
class SplunkApi(AbstractApi):
    """
    This class is the main class for calling Splunk On-Call API to generate
    custom metrics to be read by Prometheus. This class inherits from an abstract class
    to use common methods.

    The Splunk API returns data in a JSON format which requires iteration to retrieve
    desired data:
        - The Number of Incidents
        - The Number of Incidents Per team
        - Meantime to Acknowledge
        - Meantime to Resolve

    This class includes 3 major processes:
        1. Call an API to retrive data
        2. Define each metric logic as a method
        3. Implementing abstract methods to be called from the main run
    """

    def __init__(self):
        super(SplunkApi, self).__init__()

        self.config = SplunkConfig
        self.api_url = self.config.API_URL
        self.headers = {
            "X-VO-Api-Key": self.config.API_KEY,
            "X-VO-Api-Id": self.config.API_ID,
        }

        self.params = {"startedAfter": get_iso_timestamp_x_min_ago(1)}
        self.name_of_datastore = "splunk_datastore"

    def add_first_event_to_transition_dict(
        self, alert_id, transition_dict, current_event_timestamp
    ):
        if alert_id in transition_dict:
            if transition_dict[alert_id] < current_event_timestamp:
                return

        transition_dict[alert_id] = current_event_timestamp
        return None

    def create_transitions_dict(self, response):
        """
        Iteration over 'incidents' contain a list of 'transitions' which may contain
        varying length of elements as a single incident can include multiple events:
            - `trigger`
            - `acknowledge`
            - `resolved`

        The varying length of lists forces us to iterate over all elements to determine
        an event that happend FIRST.

        Dictionaries are required to keep track of each event based on a unique
        alertId to compare against other events.
        """

        # due to low volume of data, space complexity should not be an issue
        list_of_transitions = []

        time_triggered_dict = {}
        time_acknowledged_dict = {}
        time_resolved_dict = {}

        for incident in response["incidents"]:
            for transition in incident["transitions"]:
                list_of_transitions.append(transition)

        for i, transition in enumerate(list_of_transitions):
            alert_id = transition["alertId"]

            if transition["name"] == "triggered":
                time_triggered = transition["at"]
                self.add_first_event_to_transition_dict(
                    alert_id, time_triggered_dict, time_triggered
                )

            if transition["name"] == "acknowledged":
                time_acknowledged = transition["at"]
                self.add_first_event_to_transition_dict(
                    alert_id, time_acknowledged_dict, time_acknowledged
                )

            if transition["name"] == "resolved":
                time_resolved = transition["at"]
                self.add_first_event_to_transition_dict(
                    alert_id, time_resolved_dict, time_resolved
                )

        return time_triggered_dict, time_acknowledged_dict, time_resolved_dict

    def calculate_time_diff_in_min(self, list_of_time_tuples):
        list_of_time_diff = []

        for time_1, time_2 in list_of_time_tuples:
            t1 = datetime.strptime(time_1, "%Y-%m-%dT%H:%M:%S%z")
            t2 = datetime.strptime(time_2, "%Y-%m-%dT%H:%M:%S%z")

            time_diff = (t2 - t1).total_seconds() / 60

            list_of_time_diff.append(time_diff)

        return list_of_time_diff

    def create_list_of_time_diff(self, time_triggered_dict, event_action_dict):
        list_of_triggered_and_actioned_events = []

        for alert_id, triggered_time in time_triggered_dict.items():
            if alert_id in event_action_dict:
                list_of_triggered_and_actioned_events.append(
                    (triggered_time, event_action_dict[alert_id])
                )

        list_of_time_diff = self.calculate_time_diff_in_min(
            list_of_triggered_and_actioned_events
        )

        return list_of_time_diff

    @register_metric("number_of_incidents")
    @enable_delta_metric
    def get_number_of_incidents(self):
        self.params = {}  # override params to get all time total figure

        response = self.get_data_from_store(self.name_of_datastore)
        total_incidents = response["total"]

        return total_incidents

    @register_metric("time_taken_to_resolve")
    def get_time_taken_to_resolve(self):
        response = self.get_data_from_store(self.name_of_datastore)
        list_of_time_triggered_and_resolved = []

        (
            time_triggered_dict,
            time_acknowledged_dict,
            time_resolved_dict,
        ) = self.create_transitions_dict(response)

        list_of_time_diff = self.create_list_of_time_diff(
            time_triggered_dict, time_resolved_dict
        )

        if not list_of_time_diff:
            return None

        return int(statistics.mean(list_of_time_diff))

    @register_metric("time_taken_to_acknowledge")
    def get_time_taken_to_acknowledge(self):
        response = self.get_data_from_store(self.name_of_datastore)
        list_of_time_triggered_and_acknowledged = []

        (
            time_triggered_dict,
            time_acknowledged_dict,
            time_resolved_dict,
        ) = self.create_transitions_dict(response)

        list_of_time_diff = self.create_list_of_time_diff(
            time_triggered_dict, time_acknowledged_dict
        )

        if not list_of_time_diff:
            return None

        return int(statistics.mean(list_of_time_diff))
