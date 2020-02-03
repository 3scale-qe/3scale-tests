"""
Rewrite spec/functional_specs/policies/incorrect_policy_name_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.gateways import GATEWAY_CLASS
from testsuite.gateways.apicast import SystemApicastGateway


@pytest.fixture(scope="module")
def policy_settings():
    """Configure 'incorrect_name' policy which is non-existing/invalid"""

    return rawobj.PolicyConfig("incorrect_name", {"rules": []})


@pytest.fixture
def prod_client(application, testconfig, redeploy_production_gateway):
    """api_client using production gateway"""

    application.service.proxy.list().promote()
    redeploy_production_gateway()

    return application.api_client(endpoint="endpoint", verify=testconfig["ssl_verify"])


def test_incorrect_name_policy_staging_call(api_client):
    """Calls through staging gateway should be still working"""

    response = api_client.get("/get")
    assert response.status_code == 200


@pytest.mark.slow
@pytest.mark.disruptive
@pytest.mark.skipif(not issubclass(GATEWAY_CLASS, SystemApicastGateway),
                    reason="This test requires production gateway")
def test_incorrect_name_policy_production_call(prod_client):
    """Calls through production gateway should be still working"""

    response = prod_client.get("/get")
    assert response.status_code == 200
