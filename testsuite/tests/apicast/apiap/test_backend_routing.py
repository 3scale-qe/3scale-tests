"""
Test for product metrics combined with routing policy.
"""

import pytest

from testsuite import rawobj, resilient

pytestmark = [pytest.mark.nopersistence, pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3623")]


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """
    Create 2 separate backends:
       - path to Backend 1: "/echo"
       - path to Backend 2: "/quotes"
    """
    return {"/echo": custom_backend("echo"), "/quotes": custom_backend("quotes")}


@pytest.fixture(scope="module")
def proxy(service):
    """
    Returns object representing proxy bound to a service.

    Should deliver slight performance improvement
    """

    return service.proxy.list()


@pytest.fixture(scope="module")
def client(api_client, proxy):
    """
    Client without retry attempts

    This testing expect 404 returns what is handled by default retry feature.
    To avoid long time execution because of retry client without retry will be
    used. Firstly a request with retry is made to ensure all is setup.
    """

    proxy.deploy()

    assert api_client().get("/echo/anything").status_code == 200

    proxy.mapping_rules.list()[0].delete()
    proxy.deploy()

    return api_client(disable_retry_status_list={404})


@pytest.fixture(scope="module")
def backend_usages(service):
    """
    Returns backends bound to the services.

    Should deliver slight performance improvement
    """

    return service.backend_usages.list()


@pytest.fixture(scope="module")
def backend_echo(threescale, backend_usages):
    """
    First bound backend

    Should deliver slight performance improvement
    """

    return threescale.backends.read(backend_usages[0]["backend_id"])


@pytest.fixture(scope="module")
def backend_quotes(threescale, backend_usages):
    """
    Second bound backend

    Should deliver slight performance improvement
    """

    return threescale.backends.read(backend_usages[1]["backend_id"])


@pytest.fixture(scope="module")
def isolated_backends(backend_echo, backend_quotes, proxy):
    """
    Have two backends with various methods and mappings

    Use this setup
        Backend 1:
            - Add method "loud-echo"
            - Add method "low-echo"
            - Add mapping rule with path "/anything/loud" that increment "loud-echo" method
            - Add mapping rule with path "/anything/low" that increment "low-echo" method
        Backend 2:
            - Add mapping rule with path "/anything/qod" that increment default hits

    Then expect:
        - requests with invalid paths have status_code 404
        - metrics didn't increase
        - request with valid paths have status code 200
        - the right metric increase
    """

    echo_metric = backend_echo.metrics.list()[0]
    quotes_metric = backend_quotes.metrics.list()[0]

    backend_echo.mapping_rules.create(rawobj.Mapping(echo_metric, "/anything/loud"))
    backend_echo.mapping_rules.create(rawobj.Mapping(echo_metric, "/anything/low"))

    backend_quotes.mapping_rules.create(rawobj.Mapping(quotes_metric, "/anything/qod"))

    proxy.deploy()

    return proxy


@pytest.fixture(scope="module")
def empty_path(isolated_backends, backend_echo, proxy, backend_usages):  # pylint: disable=unused-argument
    """
    Have two backends configured as defined in case1.

    Make these extra modifications:
        Backend 1:
            - Add mapping rule with path "/anything/quotes/bar" that increment default hits
            - Change Product path to this backend to "/"

    Then expect:
        - Same procedure as in the previous test with different paths
    """

    echo_metric = backend_echo.metrics.list()[0]

    backend_echo.mapping_rules.create(rawobj.Mapping(echo_metric, "/anything/quotes/bar"))

    backend_usages[0].update({"path": "/"})

    proxy.deploy()

    return proxy


@pytest.fixture(scope="module")
def path_extension(empty_path, backend_usages, backend_quotes, proxy):  # pylint: disable=unused-argument
    """
    Have two backends configured as defined in case2 with additional setup.

    Make these extra modifications:
        Backend 1:
            - Change Product path to this backend to "/quotes/test"
        Backend 2:
            - Add method "test"
            - Add mapping rule with path "/test" that increment method "test"

    Then expect:
        - Same procedure as in the previous test with different paths
    """
    backend_usages[0].update({"path": "/quotes/anything/test"})

    quotes_metric = backend_quotes.metrics.list()[0]

    backend_quotes.mapping_rules.create(rawobj.Mapping(quotes_metric, "/anything/test"))

    proxy.deploy()

    return proxy


def hits(app, analytics):
    """Helper to provide access to app analytics"""
    return analytics.list_by_service(app["service_id"], metric_name="hits")["total"]


@pytest.mark.parametrize(
    "setup,expect_ok,expect_not_found",
    [
        (
            "isolated_backends",
            ["/echo/anything/loud", "/echo/anything/low", "/quotes/anything/qod"],
            ["", "/echo/anything", "/echo/"],
        ),
        (
            "empty_path",
            ["/anything/loud", "/anything/low", "/quotes/anything/qod"],
            ["", "/quotes/anything/test", "/quotes/anything/bar"],
        ),
        (
            "path_extension",
            ["/quotes/anything/test/anything/loud", "/quotes//anything/qod", "/quotes/anything/test/anything/low"],
            ["", "/quotes", "/quotes/test", "/quotes/anything/test"],
        ),
    ],
)
@pytest.mark.nopersistence  # This is a complex test that checks changes during test run hence is
# incompatible with persistence plugin
# pylint: disable=too-many-arguments
def test(request, backend_usages, application, client, setup, expect_ok, expect_not_found):
    """
    Ensure that requests against the service return appropriate value

    With accordance to setup different URL request should return either 200 or 404
    """

    request.getfixturevalue(setup)

    assert len(backend_usages) == 2

    analytics = application.threescale_client.analytics

    for path in expect_ok:
        hits_before = hits(application, analytics)

        response = client.get(path)
        assert response.status_code == 200, f"For path {path} expected status_code 200"

        hits_after = resilient.analytics_list_by_service(
            application.threescale_client, application["service_id"], "hits", "total", hits_before + 1
        )

        assert hits_before + 1 == hits_after, f"For path {path} expected hits to be increased by 1"

    for path in expect_not_found:
        hits_before = hits(application, analytics)

        response = client.get(path)
        assert response.status_code == 404, f"For path {path} expected status_code 400"

        hits_after = hits(application, analytics)
        assert hits_before == hits_after, f"For path {path} expected hits to be same before and after"
