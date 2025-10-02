"""
Testing the custom metric policy
The policy enables to decide whether to increase a
metric based on the response from the upstream API
"""

import pytest
import pytest_cases
from packaging.version import Version  # noqa # pylint: disable=unused-import
from pytest_cases import parametrize_with_cases

from testsuite.tests.apicast.policy.custom_metric import config_cases
from testsuite.utils import blame
from testsuite import rawobj, resilient, TESTED_VERSION  # noqa # pylint: disable=unused-import


pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5098"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
]


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Change api_backend to httpbin for service, as the test uses utilities provided
    only by http_bin ("/response_headers" endpoint)"
    """
    return custom_backend("backend_default", endpoint=private_base_url("httpbin"))


# pylint: disable=too-many-arguments
@pytest_cases.fixture
@parametrize_with_cases("case_data", cases=config_cases)
def config(custom_service, case_data, request, backends_mapping, lifecycle_hooks, service_proxy_settings):
    """
    Configuration for the custom metric policy
    Creates a service
    Creates metrics based on the case_data
    Adds the policy with the setting based on the case_data
    """
    service = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends=backends_mapping, hooks=lifecycle_hooks
    )

    policy_config, calls, metrics = case_data
    proxy = service.proxy.list()
    for metric in metrics:
        service.metrics.create(rawobj.Metric(metric))

    proxy.policies.insert(0, policy_config)
    proxy.deploy()

    yield service, calls, metrics
    for usage in service.backend_usages.list():
        usage.delete()


@pytest_cases.fixture
def application(config, custom_app_plan, custom_application, request):
    """
    An application bound to the service created in the config fixture
    """
    service = config[0]
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


# pylint: disable=unused-argument
@pytest_cases.fixture
def client(staging_gateway, application):
    """
    Local replacement for default api_client.
    We need it because of function scope of the application.
    We also need dependency for staging_gateway.
    """
    return application.api_client()


# pylint: disable=too-many-locals
def test_custom_policy(application, threescale, config, client):
    """
    Tests the custom policy
    For each call from the tested case
     - gets hits for the specified metrics
     - sends a request to the specified endpoint (with optional params)
     - gets hits after the request
     - asserts that the hits incremented as specified
    """

    analytics = threescale.analytics
    _, calls, metrics = config

    for status_code, increments, endpoint, params in calls:
        hits_before = []
        for metric in metrics:
            hits_before.append(analytics.list_by_service(application["service_id"], metric_name=metric)["total"])

        response = client.get(endpoint, params=params)
        assert response.status_code == status_code

        hits_after = []
        for i, metric in enumerate(metrics):
            threshold = hits_before[i] + increments[i]
            hits_after.append(
                resilient.analytics_list_by_service(threescale, application["service_id"], metric, "total", threshold)
            )

        for i, increment in enumerate(increments):
            assert hits_after[i] - hits_before[i] == increment
