"""
Test if APIAP routing only match paths that start with the routing path of the backend
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.8.1')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4736"),
]


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """
    Create backend with path "/bin"
    """
    return {"/bin": custom_backend("backend_bin")}


@pytest.fixture(scope="module")
def mapping_rules(service):
    """
    Add mapping rule with path "/test"
    """
    metric = service.metrics.list()[0]
    service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/test"))
    service.proxy.deploy()

    return service


@pytest.fixture(scope="module")
def api_client(api_client, service):
    """
    Client without retry attempts

    This testing expect 404 returns what is handled by default retry feature.
    To avoid long time execution because of retry client without retry will be
    used. Firstly a request with retry is made to ensure all is setup.
    """
    proxy = service.proxy.list()

    assert api_client().get("/bin/anything").status_code == 200

    proxy.mapping_rules.list()[0].delete()
    proxy.deploy()

    return api_client(disable_retry_status_list={404})


# pylint: disable=unused-argument
def test_apiap_routing_with_product_mapping(api_client, mapping_rules, service):
    """
    Test if:
       - Request to path "/bin/test/anything" have status_code 404 (no mapping rule at the backend level)
       - Request to path "/test/bin/anything" have status_code 404 (path doesn't start with the routing of the backend)
    """
    request = api_client.get("/bin/test/anything")
    assert request.status_code == 404
    request = api_client.get("/test/bin/anything")
    assert request.status_code == 404
