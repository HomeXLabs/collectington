# Welcome to `Collectington `

`Collectington` calls 3rd party APIs to gather data/metrics and translates those metrics for `Prometheus` to monitor


## How does it work?

- This application (Python3) can run in any environment as it can be installed using `pip` command

    `pip install collectington`

- Once the service is running, the service will make an API call every 60 sec to read data (metrics) from 3rd party services. The read data must be translated based on the logic you provide so `Prometheus` is able to monitor.

- `Collectington` uses [`Prometheus-Client`](https://github.com/prometheus/client_python#three-step-demo) and we have automated a lot of steps that require writing many lines of code. `Collectington` removes the process of:
    - Having to define logic for calling APIs
    - Instantiating prometheus client class many times
    - Mapping prometheus metric to each function using the client
    - Calculating metrics to avoid double counting
    - Caching API call response to minimize requests

- All you need to use `Collectington` is a single `json` config and a custom API class.

## How do I start using `Collectington`?

1. Install `Collectington` using the below command

    `pip install collectington`

1. Create your configuration file. [Link](https://github.com/HomeXLabs/collectington/blob/main/example/config.json)


    e.g. `config.json`

    Here's an example config file:
    ```
    {
        "api_call_intervals" : 2,
        "log_level" : "INFO",
        "services" : {
            "splunk" : {
                "service_class" : "SplunkApi",
                "service_module" : "splunk_api",
                "port" : 8000,
                "api_url" : "https://api.victorops.com/api-reporting/v2/incidents",
                "prometheus_metrics_mapping" : {
                    "counter" : [
                    "number_of_incidents"
                    ],
                    "summary" : [
                    "time_taken_to_acknowledge",
                    "time_taken_to_resolve"
                    ]
                },
                "secret_file_path" : "./splunk",
                "api_key" : "",
                "api_id" : ""
            }
        }
    }
    ```
    Let's take a closer look at this config file

    - `port` (required): the port you want to run your service.
    - `api_call_intervals` (required): the interval between each API call in seconds
    - `log_level` (required): level of logging you want. It is currently under development.
    - `services` (required):
        - There are a number of components to pay attention to. This requires a dictionary with `key` being the name of your `service`.
        Inside your `service` dictionary, below is a detailed explanation of what these are
        - `service_class` (required): this is the name of your service class that you create to define your metrics.
        - `service_module` (required): this is the name of your module or filename that contains your `service_class`
        - `api_url` (required): this is the API endpoint that you want to get data from.
        - `prometheus_metrics_mapping`(required):
            - Define `prometheus_metrics_mapping` in a `dictionary`

            - `Prometheus` client includes 4 metrics - `Counter`, `Summary`, `Histogram`, and `Gauge`:
                - The `Counter` type is useful for tracking increasing metrics (i.e. number of calls)
                - `Gauge` should be used when you want to track the exact value of a metric. We've setup `collection` to report the `observe()` value of the metric when sending to prometheus.
                - `Summary` should be used for recording statistics on aggregated values. If you have many metrics per `API_CALL_INTERVALS`, you can use summary type to get the `<METRIC>_sum`, `<METRIC>_count`, and `<METRIC>_created` on prometheus for free.
                - `Histogram` can be used similarly as `Summary` except it has different metrics aggregations (it groups by percentile buckets).
                - Please refer to the [official Prometheus client documentation](https://github.com/prometheus/client_python#instrumenting) additional details.

            - This instantiation step is automated from the `Collection Service` and can be configured from the `config` file as below:

                e.g. `number_of_instances` metric will be auto-instantiated with `Counter`
                ```
                PROMETHEUS_METRICS_MAPPING = {
                    'counter': ['number_of_incidents'],
                    'summary': ['time_taken_to_acknowledge', 'time_taken_to_resolve']
                }
                ```
        -  The rest of the config fields are completely optional. If you want to add any custom config to read from it, that is completely fine. The only optinal config that is built-in with `Collectington` is the `prometheus_metric_labels`. This fields is reserved for `collectingon` for its own use.

        - `prometheus_metric_labels` (optional):
            - This adds labels to the given metrics. Based on the above examples the labels could look like:
            ```
            "prometheus_metrics_mapping" : {
                    "counter" : [
                    "number_of_incidents"
                    ],
                    "summary" : [
                    "time_taken_to_acknowledge",
                    "time_taken_to_resolve"
                    ]
                }
            ```
            - Whenever a metric is defined with labels there are a couple of changes that **need** to be done or else the `collection` service will error. These are as follow:

                - The user-defined function in the `*_api.py` that gets metrics with labels (i.e. `get_number_of_incidents`) will need to return a different type of datastructure. It should return a `list` of `dict` that has every label as keys and one extra key that stores the actual metric value.
                    - i.e. for a metric that has labels `["team_name", "stack"]` the returned metric must look like below (even if it's only one element):
                    ```
                    [
                        {
                            "team_name": "some_label_value",
                            "stack": "prd",
                            "metric_value": 123
                        },
                        {
                            "team_name": "some_label_value",
                            "stack": "sbx",
                            "metric_value": 34
                        }
                    ]
                    ```
                    - Notice that this is different from the normal user-defined functions which return a single numeric value.
                - There should be one `dict` for each unique combination of label values; that means `team_name = some_label_value` and `stack = prd` cannot have appear a second time (from above example) since they already have a metric value.
                - The keys that correspond to the labels must match exactly (case-sensitive).
                - The key for the metric can be anything, but must be there.
                - You cannot use the `@enable_delta_metric` decorator with labeled metrics, instead change your function to calculate the delta or change the metric type to be `gauge`.

1. Create an API Class. [Link](https://github.com/HomeXLabs/collectington/blob/main/example/splunk_api.py)

    You will find an example API Class below. Let's take a look at a closer look at this file.

    ### Imports
    - The first task is to import `collectington` library. You would need `collectington.config` in order to read config properly


    - You would also need to import certain class and functions from `collectington.collectington_api` from the library
        - `enable_delta_metric` (optional): This is optional but will be useful as metrics data collected is cumulative. This will avoid double counting any metric
        - `register_metric_class` (required): This is required as you would have to register your own class to `Collectington's` metric.
        - `register_metric` (required): This allows you to register your metrics functions to be used/called by the main application.

    ### Class init
    -  There are certain fields that are required to use `collectington`.
        ```
        def __init__(self):
            super(SplunkApi, self).__init__()

            self.config = get_config("config.json")
            self.service_name = "splunk"
            ...
        ```

    - `self.config` (required): you have to provide your config path by using the `get_config` function
    - `self.service_name` (required): you have to provide your service name that matches the service name in the [config file](https://github.com/HomeXLabs/collectington/blob/a68e7337a0f843a73763cb934d18d19a13937a47/example/config.json#L6)
    - `self.headers` (optional): this is required if you need to send `header` information. `Collectington` uses the `requests` library so it works the same way.
    - `self.params` (optional): this is required if you need to add `params` to your API URL. If you need custom params for each metric method. You can simply override it from a method.
    - `self.name_of_datastore` (required): this is required as this will ensure that your API is cached and not making unnecessary calls for every metric
    - The rest of the init attributes will be different for each case. This example uses the custom utils functions to get credentials for its API key.

    ### Class Metric Methods
    - This is the core of your application. `Collectington` allows you to only worry about how to call 3rd party APIs and get the metrics. The rest is automated by `Collectington`. You just need to simply define your metric methods and register it using the imported decorator.

     - Here's how to implement Metrics in detail

        If you decide to add another service - `new_api`, you must do the following.


        -  Create a new module - e.g. `new_api.py`
            - Create a subclass called `NewApi` which inherits from the `CollectingtonApi` class.

            - Ensure that it is using  `@register_metric_class` class decorator to ensure metrics defined in your class are going to be registered to be used.

                ```
                @register_metric_class
                class NewApi(AbstractApi):
                ```

            - `CollectingtonApi` is an abstract class that includes common implementations which can be used across most services - read data, cache data, instantiate `Prometheus` metrics and etc.

            - Since the logic for each metric for each 3rd party service is different, user of the class must implement custom metrics logics from the newly created subclass.

            - You may also override common methods if you require custom implementations.

            - You must define and implement all metrics defined from the `config`

                e.g.
                ```
                def get_number_of_incidents(self):
                    response = self.get_data_from_store(self.name_of_datastore)
                    total_incidents= response['total']
                    return total_incidents
                ```

            - Once you define a metric, you must register your method using a decorator. This will ensure that the name of the metric that you defined in your config will be mapped to a correct method defined in this class.

                e.g.
                ```
                @register_metric("time_taken_to_resolve")
                def get_time_taken_to_resolve(self):
                    response = self.get_data_from_store(self.name_of_datastore)
                    list_of_time_triggered_and_resolved = []

                    ...
                ```

            - (Optional) Use `@enable_delta_metric ` decorator
                - This is to ensure that the metric you are sending to `Promteheus` is not double counted.

                - For example, let's say an API returns `1,000` which is a YTD total number of incidents. If an API is queried again after a minute and returns `1,100`, without `@enable_delta_metric`, you are sending `1,100` to Prometheus. This will result in double counting and total number of incidents will become `2,100`.

                    e.g.
                    ```
                    @register_metric("number_of_incidents")
                    @enable_delta_metric
                    def get_number_of_incidents(self):
                        response = self.get_data_from_store(self.name_of_datastore)
                        total_incidents = response["total"]
                        return total_incidents
                    ```


                - `@enable_delta_metric` will send the difference between the previous data (`1,000`) and the latest data (`1,100`) to ensure double counting is avoided.

            - (Optional) Override `_update_metric`
                - This method is to determine which `Prometheus` method will be used for each metric. If you need custom behaviour, you can override this method.

                    e.g.
                    ```
                    if isinstance(p_instance, Counter):
                        # inc is a method from Prometheus client
                        p_instance.inc(
                            service_metric_dict[metric]
                        )
                    ```


1. Once the above steps are complete, you can run the below command to spin up `Collectington`. `Collectington` has its own command line so you don't have to run the service as a python module

    `cton -s <SERVICE_NAME> -c <CONFIG_PATH>`

    - Please note that your service name must match the name defined in your config file.



## Example Service Usage

- We have in fact created a working service as an example using `Splunk` API. You can go to the [example directory](https://github.com/HomeXLabs/collectington/tree/main/example) to see it.
-  `cd` inside of the `example` directory and run the below command to see results.

    `cton -s splunk -c ./config.json`

-  Please note that since this service requires API credentials and requires to read from `splunk` file that contains the secrets, you have to create the file to run it locally in below foramt
    ```
    API_KEY="<YOUR_API_KEY>"
    API_ID="<YOUR_API_ID>"
    ```

- This is the example service class.

    ```
    ...

    from collectington.config import *
    from collectington.collectington_api import (
        CollectingtonApi,
        enable_delta_metric,
        register_metric_class,
        register_metric,
    )


    @register_metric_class
    class SplunkApi(CollectingtonApi):
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

            self.config = get_config("config.json")
            self.service_name = "splunk"
            self.api_url = self.config["services"][self.service_name]["api_url"]

            dict_of_credentials = get_credentials_from_secret_file(
                self.config["services"][self.service_name]["secret_file_path"]
            )

            self.api_id = dict_of_credentials.get("API_ID", "")
            self.api_key = dict_of_credentials.get("API_KEY", "")

            self.headers = {
                "X-VO-Api-Key": self.api_key,
                "X-VO-Api-Id": self.api_id,
            }

            self.params = {"startedAfter": get_iso_timestamp_x_min_ago(1)}
            self.name_of_datastore = "splunk_datastore"

        ...

        @register_metric("number_of_incidents")
        @enable_delta_metric
        def get_number_of_incidents(self):
            self.params = {}  # override params to get all time total figure

            response = self.get_data_from_store(self.name_of_datastore)
            total_incidents = response["total"]

            return total_incidents

        ...

    ```

## Development & Contribution

Since this is an open source project, anyone is welcome to contribute towards `Collectington`

To do development work on this project make sure you follow these steps.

1. Have your local `virtualenv` setup and add tests for each service.

1. Since we want to ensure that new features are runnable from running below,

    `pip install collectington`

    it is recommended that you create a local library to test installation and run the service.

1. You can run the below command to build a `whl` file

    `python setup.py sdist bdist_wheel`

1. Once the whl file is created, you can run `pip install <PATH_TO_YOUR_WHL_FILE>` to install the package locally.

## Testing

To run all the tests, use the virtual environment and run `python -m unittest discover`
