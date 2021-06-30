"""
Testing the propagation of internal backend api metrics to prometheus.
When an internal backend api endpoint is requested, the increase of the respective
metric is expected
"""
import base64
from time import sleep

import pytest
import requests
from packaging.version import Version  # noqa # pylint: disable=unused-import

from threescale_api.resources import Service
from testsuite.prometheus import PROMETHEUS_REFRESH
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import


NUM_OF_REQUESTS = 10

pytestmark = [
    # can not be run in parallel
    pytest.mark.disruptive,
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6453"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
]


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """
    Set auth mode to app_id/app_key, as the app_id is the id used in backend
    """
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="session")
def backend_internal_api_token(testconfig):
    """
    Returns the token for the internal api.
    The token is 'username: password' encoded in base64, where username and password
    are defined in the backend-internal-api secret
    """
    return base64.b64encode(
        f'{testconfig["threescale"]["backend_internal_api"]["username"].decode("ascii")}:'
        f'{testconfig["threescale"]["backend_internal_api"]["password"].decode("ascii")}'
        .encode("ascii")).decode("ascii")


@pytest.fixture(scope="module")
def application(application):
    """
    An application with set app limit, set to have the request querying information
    about limits return 200
    """
    service = application.service
    app_plan = service.app_plans.list()[0]
    metric = service.metrics.list()[0]
    app_plan.limits(metric).create({
        "metric_id": metric.entity_id, "period": "week", "value": 10})
    service.proxy.list().update()
    return application


@pytest.fixture(scope="module")
def auth_headers(backend_internal_api_token):
    """
    Authorization header for the backend internal api
    """
    return {"Authorization": f"Basic {backend_internal_api_token}"}


@pytest.fixture(scope="module")
def backend_listener_internal_api_endpoint(backend_listener_url, service, application,
                                           service_token):
    """
    Returns a function inserting service and a application data into a template
    internal api endpoint passed as an argument
    """
    def _backend_listener_internal_api_endpoint(endpoint):
        endpoint = endpoint.replace("{SERVICE_ID}", str(service.entity_id))\
                .replace("{APP_ID}", str(application.authobj().credentials["app_id"]))\
                .replace("{APP_PLAN_ID}", str(service.app_plans.list()[0].entity_id))\
                .replace("{METRIC_ID}", str(service.metrics.list()[0].entity_id))\
                .replace("{TOKEN}", service_token)
        return backend_listener_url + "/internal" + endpoint
    return _backend_listener_internal_api_endpoint


def internal_backend_api_query(request_type):
    """
    Returns prometheus query for the apisonator_listener_internal_api_response_codes metric
    with the request type passed in the parameters
    """
    return f"apisonator_listener_internal_api_response_codes{{request_type=\"{request_type}\"}}"


@pytest.fixture(scope="module")
def data():
    """
    Data for testing
    For each prometheus metric, there is a list of 3-tuples of method, endpoint and expected response code.
    Not using parametrized testcase to avoid waiting 30s for prometheus to load metrics for each testcase
    """
    return {
        "alerts":
            [("GET", "/services/{SERVICE_ID}/alert_limits/", "2xx"),
             ("POST", "/services/{SERVICE_ID}/alert_limits/", "4xx"),
             ("DELETE", "/services/{SERVICE_ID}/alert_limits/INVALID_ID", "404")
             ],
        "application_keys":
            [("GET", "/services/{SERVICE_ID}/applications/{APP_ID}/keys/", "2xx"),
             ("GET", "/services/{SERVICE_ID}/applications/INVALID_ID/keys/", "404"),
             ],
        "application_referrer_filters":
            [("GET", "/services/{SERVICE_ID}/applications/{APP_ID}/referrer_filters", "2xx"),
             ("GET", "/services/{SERVICE_ID}/applications/INVALID_ID/referrer_filters", "404"),
             ("POST", "/services/{SERVICE_ID}/applications/{APP_ID}/referrer_filters", "4xx"),
             ],
        "applications":
            [("GET", "/services/{SERVICE_ID}/applications/{APP_ID}", "2xx"),
             ("GET", "/services/{SERVICE_ID}/applications/INVALID_ID", "404"),
             ("POST", "/services/{SERVICE_ID}/applications/INVALID_ID", "4xx")
             ],
        "errors":
            [("GET", "/services/{SERVICE_ID}/errors/", "2xx"),
             ("GET", "/services/INVALID_ID/errors/", "404"),
             ],
        "events":
            [("GET", "/events/", "2xx"),
             ("DELETE", "/events/INVALID_ID", "404"),
             ],
        "metrics":
            [("GET", "/services/{SERVICE_ID}/metrics/{METRIC_ID}", "2xx"),
             ("GET", "/services/INVALID_ID/metrics/INVALID_ID", "404"),
             ("POST", "/services/{SERVICE_ID}/metrics/{METRIC_ID}", "4xx"),
             ],
        "service_tokens":
            [("HEAD", "/service_tokens/{TOKEN}/{SERVICE_ID}/", "2xx"),
             ("HEAD", "/service_tokens/INVALID_TOKEN/{SERVICE_ID}/", "404"),
             ("POST", "/service_tokens/", "4xx")
             ],
        "services":
            [("GET", "/services/{SERVICE_ID}", "2xx"),
             ("GET", "/services/INVALID_ID", "404"),
             ("POST", "/services/", "4xx"),
             ],
            }


@pytest.fixture(scope="module")
def data_xfail():
    """
    https://issues.redhat.com/browse/THREESCALE-6453
    Metrics and endpoints that are currently not propagated to prometheus
    Can be included in data after the issue is solved
    """
    return {
        "stats":
            [("GET", "/services/{SERVICE_ID}/stats/", "404")],
        # no mapping in source to 2xx endpoint
        # https://github.com/3scale/apisonator/blob/master/app/api/internal/stats.rb
        "usage_limits":
            [("GET", "/services/{SERVICE_ID}/plans/{APP_PLAN_ID}/usagelimits/{METRIC_ID}/week", "2xx"),
             ("GET", "/services/{SERVICE_ID}/plans/{APP_PLAN_ID}/usagelimits/{INVALID_ID}/week", "404"),
             ],
        "utilization":
            [("GET", "/services/{SERVICE_ID}/applications/{APP_ID}/utilization/", "2xx"),
             ("GET", "/services/{SERVICE_ID}/applications/INVALID_ID/utilization/", "404"),
             ],
        }


def test_internal_backend_listener(data, prometheus_response_codes_for_metric,
                                   auth_headers, backend_listener_internal_api_endpoint):
    """
    Sends a number of requests to each backend internal api endpoint.
    Asserts that the metric for the number of requests to the endpoint in prometheus is increased

    Some requests are not returning 2xx responses but 404 instead, this should not be issue with the testing the
    prometheus integration, as responses with all response codes are reported in prometheus
    """
    # wait to update metrics triggered by previous tests
    sleep(PROMETHEUS_REFRESH)

    count_before = dict()
    for request_type in data:
        count_before[request_type] = prometheus_response_codes_for_metric(internal_backend_api_query(request_type))
        for method, endpoint, response_code in data[request_type]:
            formatted_endpoint = backend_listener_internal_api_endpoint(endpoint)

            for _ in range(NUM_OF_REQUESTS):
                response = requests.request(method, formatted_endpoint, headers=auth_headers)
                response_code = response_code.replace("xx", "00")
                assert str(response.status_code) == response_code, \
                    f"failed for {request_type}, \n" \
                    f"expected response code: {response_code} \n"\
                    f"actual response_code: {response.status_code}"

    # wait to update metrics in prometheus
    sleep(PROMETHEUS_REFRESH)

    count_after = dict()
    results = dict()

    for request_type in data:
        count_after[request_type] = prometheus_response_codes_for_metric(internal_backend_api_query(request_type))
        for _, _, response_code in data[request_type]:
            # assertion is not used here to collect results for all metrics to better investigate potential errors
            results[request_type+response_code] = \
                response_code in count_after[request_type] and \
                ((response_code not in count_before[request_type] and int(count_after[request_type][response_code]) ==
                  NUM_OF_REQUESTS) or
                    int(count_after[request_type][response_code]) - int(count_before[request_type][response_code])
                 == NUM_OF_REQUESTS)

    for request_type_response_code in results.values():
        assert request_type_response_code, f"{results}"
