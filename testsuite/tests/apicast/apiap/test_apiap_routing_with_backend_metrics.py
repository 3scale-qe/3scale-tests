"""
Test apiap routing combined with metrics counting
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

# case[N] fixtures create tests that have to be executed in specific order
pytestmark = [
    pytest.mark.disruptive,
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3623"),
]


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """
    Create 2 separate backends:
        - path to Backend 1: "/"
        - path to Backend 2: "/anything"
    """
    return {"/": custom_backend("slash"), "/anything": custom_backend("anything")}


@pytest.fixture(scope="module")
def backend_slash(backends_mapping):
    """
    :return: slash backend
    """
    return list(backends_mapping.values())[0]


@pytest.fixture(scope="module")
def backend_anything(backends_mapping):
    """
    :return: Anything backend
    """
    return list(backends_mapping.values())[1]


@pytest.fixture(scope="module")
def client(api_client, service):
    """
    1. Test if request with default session have status code 200
    2. Delete default service mapping rule
    3. Create session without retry for session
    """

    assert api_client().get("/get").status_code == 200

    proxy = service.proxy.list()
    proxy.mapping_rules.list()[0].delete()
    proxy.deploy()

    return api_client(disable_retry_status_list={404})


@pytest.fixture(scope="module")
def setup(service, backend_slash, backend_anything):
    """
    Backend 1:
        - Add method "loud-method"
        - Add method "low-method"
        - Add mapping rule with path "/anything/bar" that increment default hits
        - Add mapping rule with path "/anything/loud" that increment "loud-method" method
        - Add mapping rule with path "/anything/low" that increment "low-method" method
    Backend 2:
        - Add method "test"
        - Add mapping rule with path "/anything/qod" that increment default hits
    """
    # slash backend
    slash_metric = backend_slash.metrics.list()[0]
    loud_method = slash_metric.methods.create(rawobj.Method("loud-method"))
    low_method = slash_metric.methods.create(rawobj.Method("low-method"))

    # mapping rules of slash backend
    backend_slash.mapping_rules.create(rawobj.Mapping(slash_metric, "/anything/bar"))
    backend_slash.mapping_rules.create(rawobj.Mapping(loud_method, "/anything/loud"))
    backend_slash.mapping_rules.create(rawobj.Mapping(low_method, "/anything/low"))

    # Anything backend
    anything_metric = backend_anything.metrics.list()[0]
    test = anything_metric.methods.create(rawobj.Method("test"))

    # mapping rule of anything backend
    backend_anything.mapping_rules.create(rawobj.Mapping(anything_metric, "/anything/qod"))

    service.proxy.deploy()

    return slash_metric, loud_method, low_method, anything_metric, test


# pylint: disable=too-many-locals
def get_analytics(application, backend_slash, backend_anything, setup):
    """
    Get product and backends analytics
    """
    slash_metric, loud_method, low_method, anything_metric, test = setup

    analytics = application.threescale_client.analytics

    hits = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    hits_slash = analytics.list_by_backend(backend_slash.entity_id, metric_name=slash_metric.entity_name)["total"]
    hits_loud_method = analytics.list_by_backend(backend_slash.entity_id, metric_name=loud_method.entity_name)["total"]
    hits_low_method = analytics.list_by_backend(backend_slash.entity_id, metric_name=low_method.entity_name)["total"]
    hits_anything = analytics.list_by_backend(backend_anything.entity_id, metric_name=anything_metric.entity_name)[
        "total"
    ]
    hits_anything_test = analytics.list_by_backend(backend_anything.entity_id, metric_name=test.entity_name)["total"]

    return hits, hits_slash, hits_loud_method, hits_low_method, hits_anything, hits_anything_test


@pytest.fixture(scope="module")
def case1():
    """
    :path: '/anything/bar'
    :status_code: 404
    :metrics: didn't increase
    """
    return "/anything/bar", 404, [0, 0, 0, 0, 0, 0]


@pytest.fixture(scope="module")
def case2(service):
    """
    Change path to backend slash to '/anything/test'
    :path: '/anything/test/anything/loud'
    :status_code: 200
    :metrics: product hits, slash backend hits and loud method increase, rest didn't increase
    """
    service.backend_usages.list()[0].update({"path": "/anything/test"})
    service.proxy.deploy()
    return "/anything/test/anything/loud", 200, [1, 1, 1, 0, 0, 0]


@pytest.fixture(scope="module")
def case3(service, setup, backend_anything):
    """
    Add mapping rule to anything backend with path '/anything/test'
    :path: '/anything/test'
    :status_code: 404
    :metrics: didn't increase
    """
    _, _, _, _, test = setup
    backend_anything.mapping_rules.create(
        {"http_method": "GET", "pattern": "/anything/test", "metric_id": test["id"], "delta": 1}
    )
    service.proxy.deploy()
    return "/anything/test", 404, [0, 0, 0, 0, 0, 0]


@pytest.fixture(scope="module")
def case4():
    """
    :path: '/anything/test/anything/low'
    :status_code: 200
    :metrics: product hits, slash backend hits and low method increase, rest didn't increase
    """
    return "/anything/test/anything/low", 200, [1, 1, 0, 1, 0, 0]


# pylint: disable=too-many-arguments, too-many-locals
@pytest.mark.parametrize("case", ["case1", "case2", "case3", "case4"])
def test_metrics_with_routing_policy(request, client, setup, application, backend_slash, backend_anything, case):
    """
    Test metrics counting combined with Routing Policy
    Test if:
        - Case 1:
            - request with path "/anything/bar" have status code 404
            - metrics didn't increase
        - Case 2:
            - request with path "/anything/test/anything/loud" have status code 200
            - only the right metrics increase
        - Case 3:
            - request with path "/anything/test" have status code 404
            - metrics didn't increase
        - Case 4:
            - request with path "/anything/test/anything/loud" have status code 200
            - only the right metrics increase
    """
    case = request.getfixturevalue(case)

    path, status_code, metrics = case

    (
        hits_before,
        hits_slash_before,
        hits_loud_method_before,
        hits_low_method_before,
        hits_anything_before,
        hits_anything_test_before,
    ) = get_analytics(application, backend_slash, backend_anything, setup)

    request = client.get(path)

    (
        hits_after,
        hits_slash_after,
        hits_loud_method_after,
        hits_low_method_after,
        hits_anything_after,
        hits_anything_test_after,
    ) = get_analytics(application, backend_slash, backend_anything, setup)

    assert request.status_code == status_code
    assert hits_before + metrics[0] == hits_after
    assert hits_slash_before + metrics[1] == hits_slash_after
    assert hits_loud_method_before + metrics[2] == hits_loud_method_after
    assert hits_low_method_before + metrics[3] == hits_low_method_after
    assert hits_anything_before + metrics[4] == hits_anything_after
    assert hits_anything_test_before + metrics[5] == hits_anything_test_after
