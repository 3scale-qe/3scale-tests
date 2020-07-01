"""
Testing the custom metric policy
https://issues.redhat.com/browse/THREESCALE-5098
"""

from pytest_cases import fixture_plus, cases_data

from testsuite.tests.apicast.policy.custom_metric import config_cases
from testsuite.utils import blame
from testsuite import rawobj


@fixture_plus
@cases_data(module=config_cases)
def config(custom_service, case_data, request, service_proxy_settings, lifecycle_hooks):
    """
    Configuration for the custom metric policy
    Creates a service
    Creates metrics based on the case_data
    Adds the policy with the setting based on the case_data
    """
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks)

    policy_config, calls, metrics = case_data.get()
    proxy = service.proxy.list()
    for metric in metrics:
        service.metrics.create(rawobj.Metric(metric))
    proxy.update()

    proxy.policies.insert(0, policy_config)

    return service, calls, metrics


@fixture_plus
def application(config, custom_app_plan, custom_application, request):
    """
    An application bound to the service created in the config fixture
    """
    service = config[0]
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


# pylint: disable=too-many-locals
def test_custom_policy(application, threescale, config):
    """
    Tests the custom policy
    For each call from the tested case
     - gets hits for the specified metrics
     - sends a request to the specified endpoint (with optional params)
     - gets hits after the request
     - asserts that the hits incremented as specified
    """
    api_client = application.api_client()

    analytics = threescale.analytics
    metrics = config[2]
    calls = config[1]

    for status_code, increments, endpoint, params in calls:
        hits_before = []
        for metric in metrics:
            hits_before.append(analytics.list_by_service(application["service_id"], metric_name=metric)["total"])

        response = api_client.get(endpoint, params=params)
        assert response.status_code == status_code

        hits_after = []
        for metric in metrics:
            hits_after.append(analytics.list_by_service(application["service_id"], metric_name=metric)["total"])

        for i, increment in enumerate(increments):
            assert hits_after[i] - hits_before[i] == increment
