"""
Tests wasm mapping rules special handling.
"""
import backoff
import pytest
from testsuite.capabilities import Capability
from testsuite import rawobj
from testsuite.utils import blame


pytestmark = pytest.mark.required_capabilities(Capability.SERVICE_MESH_WASM)


def set_mapping_rules(service, metric_name):
    """Deletes implicit '/' rule and sets new for path '/anything/something'"""
    proxy = service.proxy.list()
    proxy.mapping_rules.delete(proxy.mapping_rules.list()[0]["id"])  # delete implicit "/" rule
    metric = service.metrics.create(rawobj.Metric(metric_name))
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/something"))
    proxy.deploy()


@backoff.on_exception(backoff.constant, AssertionError, interval=10, max_tries=6, jitter=None)
def backoff_request(client, url, expected_return):
    """
    Get request which retries for max a minute if unexpected status code is returned.
    """
    assert client.get(url).status_code == expected_return


def test_mapping_rules_automatic_sync(api_client, service, request):
    """
    Wasm synchronizes mapping rules from 3scale periodically. Usually every 20-60s.
    This test changes mapping rules in proxy config and waits for wasm to sync.
    Then tests if only '/anything/something' path returns 200 meaning synchronisation was successful.
    """
    client = api_client(disable_retry_status_list=[404])

    assert client.get("/anything/anything").status_code == 200

    set_mapping_rules(service, blame(request, "Metric"))
    backoff_request(client, "/anything/anything", expected_return=404)  # waiting for synchronisation

    assert client.get("/anything/anything").status_code == 404
    assert client.get("/anything/something").status_code == 200
