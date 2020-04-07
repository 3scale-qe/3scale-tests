"""
Test if APIAP routing only match paths that contain whole routing path
https://issues.redhat.com/browse/THREESCALE-4904
"""
import pytest
import requests
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """
    Create 2 separate backends:
        - path to Backend 1: "/test/bin"
        - path to Backend 2: "/bin"
    """
    return {"/test/bin": custom_backend("backend_test"), "/bin": custom_backend("backend_bin")}


@pytest.fixture(scope="module")
def mapping_rules(service, threescale):
    """
    Backend 1:
        - Add mapping rule with path "/anything/test"
    Backend 2:
        - Add mapping rule with path "/anything/bin"
    """
    backends = service.backend_usages.list()
    backend_test = threescale.backends.read(backends[0]["backend_id"])
    test_metric = backend_test.metrics.list()[0]
    backend_bin = threescale.backends.read(backends[1]["backend_id"])
    bin_metric = backend_bin.metrics.list()[0]
    backend_test.mapping_rules.create(rawobj.Mapping(test_metric, "/anything/test"))
    backend_bin.mapping_rules.create(rawobj.Mapping(bin_metric, "/anything/bin"))
    service.proxy.list().update()


@pytest.fixture(scope="module")
def api_client(application):
    """
    Client without retry attempts

    This testing expect 404 returns what is handled by default retry feature.
    To avoid long time execution because of retry client without retry will be
    used. Firstly a request with retry is made to ensure all is setup.
    """
    assert application.api_client().get("/bin/anything/bin").status_code == 200

    session = requests.Session()
    session.auth = application.authobj
    return application.api_client(session=session)


# pylint: disable=unused-argument
def test_apiap_routing_to_backend(api_client, mapping_rules, service):
    """
    Test if:
        - request with path "/test/bin/anything/test" have status code 200
        - request with path "/bin/anything/bin" have status code 200
        - request with path "/test/bin/anything/bin" have status code 404
        - request with path "/bin/anything/test" have status code 404
    """
    backends = service.backend_usages.list()
    assert len(backends) == 2
    request = api_client.get("/test/bin/anything/test")
    assert request.status_code == 200
    request = api_client.get("/bin/anything/bin")
    assert request.status_code == 200
    request = api_client.get("/test/bin/anything/bin")
    assert request.status_code == 404
    request = api_client.get("/bin/anything/test")
    assert request.status_code == 404
