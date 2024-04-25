"""
Rewrite: /spec/functional_specs/mapping_rules_matching_order_with_multibackend_spec.rb

When having multiple backends where the path of the later is being a subset of
the previous one and same mapping is set to these backends, assure that the
traffic is correctly distributed between the backends.

When having a backend with a mapping rule with the 'last' flag set to true,
the request matching that mapping rule is not evaluated by other mapping rules.
"""

import pytest

from testsuite import rawobj
from testsuite import resilient

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Creates four echo-api backends with the private paths being the keys in
    the dict
    """
    return {
        "/backpath1": custom_backend("backend1", endpoint=private_base_url("echo_api")),
        "/backpath2/backpath21/backpath22": custom_backend("backend2", endpoint=private_base_url("echo_api")),
        "/backpath2/backpath21": custom_backend("backend3", endpoint=private_base_url("echo_api")),
        "/backpath2": custom_backend("backend4", endpoint=private_base_url("echo_api")),
    }


@pytest.fixture(scope="module")
def proxy(service):
    """
    Returns object representing proxy bound to a service.
    Should deliver slight performance improvement
    """
    return service.proxy.list()


@pytest.fixture(scope="module")
def delete_mapping(proxy):
    """Deletes all current mapping on the product level"""
    proxy.deploy()
    proxy.mapping_rules.list()[0].delete()
    proxy.deploy()


@pytest.fixture(scope="module")
# pylint: disable=unused-argument
def client(application, delete_mapping, api_client):
    """
    Client configured not to retry requests.

    By default, the failed requests are retried by the api_client.
    As 404 is the desired outcome of one of the tests, the client is
    configured not to retry requests to avoid long time execution.
    """

    application.test_request()  # ensure all is up and ready

    return api_client(disable_retry_status_list={404})


@pytest.fixture(scope="module")
def backend_usages(service):
    """
    Returns backends bound to the services.
    Should deliver slight performance improvement
    """
    return service.backend_usages.list()


@pytest.fixture(scope="module")
def backend1(threescale, backend_usages):
    """
    First bound backend
    Should deliver slight performance improvement
    """
    return threescale.backends.read(backend_usages[0]["backend_id"])


@pytest.fixture(scope="module")
def backend2(threescale, backend_usages):
    """
    Second bound backend
    Should deliver slight performance improvement
    """
    return threescale.backends.read(backend_usages[1]["backend_id"])


@pytest.fixture(scope="module")
def backend3(threescale, backend_usages):
    """
    Second bound backend
    Should deliver slight performance improvement
    """
    return threescale.backends.read(backend_usages[2]["backend_id"])


@pytest.fixture(scope="module")
def backend4(threescale, backend_usages):
    """
    Second bound backend
    Should deliver slight performance improvement
    """
    return threescale.backends.read(backend_usages[3]["backend_id"])


@pytest.fixture(scope="module")
def backends(backend1, backend2, backend3, backend4, proxy):
    """
    Adds the mapping rules to the backends.

    The sets the 'last' flag of the first mapping rule to 'true'

    """
    backend1_metric = backend1.metrics.list()[0]

    backend1.mapping_rules.create(rawobj.Mapping(backend1_metric, "/path1/bar", last="true"))
    backend1.mapping_rules.create(rawobj.Mapping(backend1_metric, "/path1/bar/{id}"))

    for backend in (backend2, backend3, backend4):
        metric = backend.metrics.list()[0]

        backend.mapping_rules.create(rawobj.Mapping(metric, "/path1/{id}"))
        backend.mapping_rules.create(rawobj.Mapping(metric, "/{id}"))
        backend.mapping_rules.create(rawobj.Mapping(metric, "/"))

    proxy.deploy()


def hits(app):
    """Helper to provide access to app analytics"""
    analytics = app.threescale_client.analytics

    return analytics.list_by_service(app["service_id"], metric_name="hits")["total"]


@pytest.mark.parametrize(
    "expect_ok",
    [
        (
            [
                ("/backpath2/backpath21/backpath22/path1/1234", 3),
                ("/backpath2/backpath21/backpath22/path1", 2),
                ("/backpath2/backpath21/backpath22/", 1),
                ("/backpath2/backpath21/path1/1234", 3),
                ("/backpath2/backpath21/path1", 2),
                ("/backpath2/backpath21/", 1),
                ("/backpath2/path1/1234", 3),
                ("/backpath2/path1", 2),
                ("/backpath2/", 1),
                ("/backpath1/path1/bar/1234", 1),
                ("/backpath1/path1/bar", 1),
            ]
        )
    ],
)
# pylint: disable=unused-argument
def test(application, client, backend_usages, backends, expect_ok):
    """
    Make requests against all backends and mappings
    Assert that these requests return 200
    Assert that the hits were increased by the correct number, according
    to number of mapped endpoints with same prefix and the setting of the last
    flag
    """
    # tests the hits at product level, when the
    # https://issues.redhat.com/browse/THREESCALE-3159 is finished
    # it will be also possible to check the hits at the backend level
    # right now is by hits only tested if the 'last' flag in mapping at
    # the backend level works correctly
    for path, expected_hits_diff in expect_ok:
        hits_before = hits(application)

        response = client.get(path)
        assert response.status_code == 200, f"For path {path} expected status_code 200"

        hits_after = resilient.analytics_list_by_service(
            application.threescale_client, application["service_id"], "hits", "total", hits_before + expected_hits_diff
        )
        assert hits_after == hits_before + expected_hits_diff, f"For {path} expected different number of hits"
