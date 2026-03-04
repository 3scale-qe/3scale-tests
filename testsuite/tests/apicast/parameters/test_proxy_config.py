"""
Test for issue https://issues.redhat.com/browse/THREESCALE-8485
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.sandbag,
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8485"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.13')"),
]


@pytest.fixture(scope="module")
def staging_gateway(staging_gateway):
    """Sets environment for test"""
    staging_gateway.environ["APICAST_LOAD_SERVICES_WHEN_NEEDED"] = True
    staging_gateway.environ["APICAST_CONFIGURATION_LOADER"] = "lazy"

    return staging_gateway


def test_proxy_config(service, api_client):
    """
    Preparation:
        - Create service
        - Create 500+ proxy configs for that service
        - Delete default mapping rule and create new one
    Test:
        - that creation of new mapping rule was correctly promoted.
    """
    endpoint = service.proxy.list()["endpoint"]

    for i in range(505):
        service.proxy.update(params={"endpoint": f"https://anything{i}.invalid:80"})

    service.proxy.update(params={"endpoint": endpoint})

    metric = service.metrics.list()[0]
    mapping_rules = service.proxy.mapping_rules

    mapping_rules.list()[0].delete()
    mapping_rules.create(rawobj.Mapping(metric, pattern="/foo"))
    service.proxy.deploy()

    client = api_client()

    response = client.get("/boo")
    assert response.status_code == 404

    response = client.get("/foo")
    assert response.status_code == 200
