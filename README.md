## Welcome to `Collection Service`

Collection service scrapes 3rd party metrics and translates those metrics for `Prometheus` to monitor


### How does it work?

- This application (Python3) is meant to run as part of `Kubernetes` clusters and must be run with an argument that represents your service.

    e.g. `python3 -m src.runner -s splunk`

- Once the service is launched, the service will make an API call every 60 sec to read data (metrics) from 3rd party services. The read data must be translated based on the logic you provide so `Prometheus` is able to monitor.

- It is important to understand [`Prometheus-Client`](https://github.com/prometheus/client_python#three-step-demo) to fully utilize this service. We cannot simply pass a `JSON` object for `Prometheus` to read and parse data like the traditional APIs. We have to define and continuously send data for each metric one by one using the `Prometheus` Client API.


<strong>IMPORTANT: Please note that the below steps are likely to CHANGE in the near future to further simplify the usage of the `Collection Service` </strong>

### Configuration

Configuration must be done from `configs.config.py`. Please see below for detailed steps.

1. `BaseConfig`
    - `BaseConfig` class contains common configs.

1. `ServiceConfig`
    - Define your own config as below:
    `<Service>Config` e.g. `SplunkConfig`

    Please note that using only <strong>one word</strong> for the service name is currently supported.
    e.g. `SnowflakeConfig` instead of `SnowFlakeConfig`

1. `Constants`
    - Define `constants` that are specific to your application. Examples includes `AWS` credentials - `API_KEY`, `API_ID`...

1. `AVAILABLE_METRICS`
    - Define `AVAILABLE_METRICS` in a `list`
    - These are the name of the metrics that will be used for creating `Prometheus` client instances.
        e.g.
        ```
        AVAILABLE_METRICS = [
        'number_of_incidents',
        'time_taken_to_acknowledge',
        'time_taken_to_resolve'
        ]
        ```

1. `PROMETHEUS_METRICS_MAPPING`
    - Define `PROMETHEUS_METRICS_MAPPING` in a `dictionary`

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

1. `PROMETHEUS_METRIC_LABELS`
    - This adds labels to the given metrics. Based on the above examples the labels could look like:
    ```
    PROMETHEUS_METRIC_LABELS = {
        'number_of_incidents': ["team_name", "stack"],
        'time_taken_to_acknowledge': ["team_name", "stack"],
        'time_taken_to_resolve': ["team_name", "stack"]
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


### Metrics Implementation

If you decide to add another service - `new_api`, you must do the following.

1. Add a new condition block for your new service inside `api_factory.py` to return your new service class `NewApi`

    e.g.
    ```
    class ApiFactory:

        @classmethod
        def get_api_factory(self, service):
            if service == 'splunk':
                return SplunkApi()
            elif service == 'newapi': # this block is your change
                return NewApi()
            else:
                return
    ```

1. Create a new module - e.g. `new_api.py`
    - Create a subclass called `NewApi` which inherits from the `AbstractApi` class.

    - Ensure that it is using  `@register_metric_class` class decorator to ensure metrics defined in your class are going to be registered to be used.

        ```
        @register_metric_class
        class NewApi(AbstractApi):
        ```

    - `AbstractApi` is an abstract class that includes common implementations which can be used across most services - read data, cache data, instantiate `Prometheus` metrics and etc.

    - Since the logic for each metric for each 3rd party service is different, user of the class must implement custom metrics logics from the newly created subclass.

    - You may also override common methods if you require custom implementations.

    - You must define and implement all metrics defined from the `config`
    (`AVAILABLE_METRICS`)

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

### Running the service

Once you've completed the above steps, you can run the service using the below command

e.g. `python3 -m src.runner -s splunk`

Please note that the name of the service must match the name defined in the config class

### Development

To do development work on this project make sure you have your local virtualenv setup and add tests for each new service you create.
Ensure you set environment variables as below

e.g. `source env/local.env`

### Testing

To run all the tests, use the virtual environment and run `python -m unittest discover`
