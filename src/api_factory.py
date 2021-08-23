from src.splunk_api import *

class ApiFactory:
    @classmethod
    def get_api_factory(self, service):
        if service == "splunk":
            return SplunkApi()
        else:
            return
