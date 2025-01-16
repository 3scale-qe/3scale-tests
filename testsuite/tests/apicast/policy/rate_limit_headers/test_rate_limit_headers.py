"""
Tests that:
 - information about the remaining limits should be sent in the headers.
 - information about the limit with less remaining units should be given.
 - the policy should work also on backend metrics
 - the combination of backend and service metrics should make no problem
"""

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest
import pytest_cases
from pytest_cases import fixture_ref

from testsuite.utils import blame, wait_interval
from testsuite import rawobj
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import


# rate-limit have been always unstable, likely because of overhead in staging apicast?
pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3795"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.flaky,
]


@pytest_cases.fixture
def service2(custom_service, service_proxy_settings, request, lifecycle_hooks, backends_mapping):
    """
    Function-scoped service with the rate limit headers policy
    The caching policy is added, so the reported numbers will be 100% accurate
    """

    svc = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )

    proxy = svc.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("rate_limit_headers", {}))
    proxy.policies.insert(0, rawobj.PolicyConfig("caching", {"caching_type": "none"}))

    yield svc
    for usage in svc.backend_usages.list():
        usage.delete()


@pytest_cases.fixture
def app_plan_backend(service2, backend_usages, custom_app_plan, threescale, request):
    """
    Creates a mapped metric on a backend and on a service, so the default 'hits', that are
    interconnected are not used.
    Creates an app plan with a limits on those metric, one 'minute' and the other 'hour' scoped.
    """
    backend = threescale.backends.read(backend_usages[0]["backend_id"])
    backend_metric = backend.metrics.list()[0]
    backend.mapping_rules.create(rawobj.Mapping(backend_metric, "/anything"))

    service_metric = service2.metrics.create(rawobj.Metric("metric_svc"))
    proxy = service2.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(service_metric, pattern="/anything/foo"))
    proxy.deploy()

    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app")), service2)
    plan.limits(backend_metric).create({"metric_id": backend_metric["id"], "period": "minute", "value": 10})
    plan.limits(service_metric).create({"metric_id": service_metric["id"], "period": "minute", "value": 5})

    return plan


@pytest_cases.fixture
def app_plan_service(service2, custom_app_plan, request):
    """
    Creates metrics and mapping rules for those metrics.
    The second mapping rule is a subset of the first one. When the second (foo) metric is increased,
    so is the first metric

    Creates an app plan with two limits on the created metrics.
    """
    metric_anything = service2.metrics.create(rawobj.Metric("anything"))
    metric_anything_foo = service2.metrics.create(rawobj.Metric("foo"))

    proxy = service2.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(metric_anything, pattern="/anything"))
    proxy.mapping_rules.create(rawobj.Mapping(metric_anything_foo, pattern="/anything/foo"))
    proxy.deploy()

    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app")), service2)
    plan.limits(metric_anything).create({"metric_id": metric_anything["id"], "period": "minute", "value": 10})
    plan.limits(metric_anything_foo).create({"metric_id": metric_anything_foo["id"], "period": "minute", "value": 5})

    return plan


@pytest_cases.fixture
@pytest_cases.parametrize("app_plan", [fixture_ref(app_plan_service), fixture_ref(app_plan_backend)])
def application(app_plan, custom_application, request, lifecycle_hooks):
    """
    Creates an application with a application plan defined in the specified fixture
    """
    application = custom_application(rawobj.Application(blame(request, "limited_app"), app_plan), hooks=lifecycle_hooks)

    return application


@pytest_cases.fixture
def client(application):
    """Fixture plus api client"""
    return application.api_client()


def test_rate_limit_headers(client):
    """
    - Sends three requests to the api.
    - Asserts that the information about limits from RateLimit headers is correct
    """

    # prevents refreshing limits in the middle of the test
    wait_interval()

    for i in range(3):
        response = client.get("/anything")
        assert response.status_code == 200
        assert "RateLimit-Limit" in response.headers
        assert "RateLimit-Remaining" in response.headers
        assert "RateLimit-Reset" in response.headers

        assert int(response.headers["RateLimit-Limit"]) == 10, f"The response rate limits failed on the {i} call"
        assert int(response.headers["RateLimit-Remaining"]) == 10 - i - 1
        assert int(response.headers["RateLimit-Reset"]) <= 60


def test_rate_limit_multiple_mapping_rules(client):
    """
    - Sends a request increasing both the foo and the anything metric
    - Asserts that the RateLimits for the foo metric (the more constrained one) are sent

    - Sends a number (7) of requests increasing just the anything metric,
      decreasing the number of remaining requests
    - The anything metric has now less remaining hits than the foo metric

    - Sends a request increasing both the foo and the anything metric
    - Asserts that the RateLimits for the anything metric (currently the more constrained) one are sent

    """

    wait_interval()

    response = client.get("/anything/foo")

    assert response.status_code == 200
    assert int(response.headers["RateLimit-Limit"]) == 5
    assert int(response.headers["RateLimit-Remaining"]) == 4
    assert int(response.headers["RateLimit-Reset"]) <= 60

    for _ in range(7):
        assert client.get("/anything").status_code == 200

    response = client.get("/anything/foo")

    assert response.status_code == 200
    assert int(response.headers["RateLimit-Limit"]) == 10
    assert int(response.headers["RateLimit-Remaining"]) == 1  # 10 - 1 - 7 - 1
    assert int(response.headers["RateLimit-Reset"]) <= 60
