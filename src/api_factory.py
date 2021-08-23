from src.splunk_api import *
from src.callrail_api import *
from src.deadmanswitch_api import DeadmanswitchApi
from src.dataplatformmonitoring_api import DataplatformmonitoringApi


class ApiFactory:
    @classmethod
    def get_api_factory(self, service):
        pass