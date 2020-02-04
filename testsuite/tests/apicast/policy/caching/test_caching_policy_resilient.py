"""
Rewrite spec/functional_specs/policies/caching/caching_resilient_policy_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.gateways import GATEWAY_CLASS, SystemApicastGateway


@pytest.fixture(scope="module")
def policy_settings():
    "Add caching policy configured as 'caching_type': 'resilient'"
    return rawobj.PolicyConfig("caching", {"caching_type": "resilient"})


@pytest.fixture
def prod_client(application, testconfig, redeploy_production_gateway):
    "Promote API to the production gateway"

    application.service.proxy.list().promote(version=2)
    redeploy_production_gateway()

    return application.api_client(endpoint="endpoint", verify=testconfig["ssl_verify"])


@pytest.mark.disruptive
@pytest.mark.skipif(not issubclass(GATEWAY_CLASS, SystemApicastGateway),
                    reason="This test requires production gateway")
def test_caching_policy_resilient(prod_client, openshift):
    """
    Test caching policy with caching mode set to Resilient

    To cache credentials:
        - make request to production gateway with valid credentials
    Scale backend-listener down
    Test if:
        - response with valid credentials have status_code == 200
        - after an unsuccessful response the following response will have status code 200
    Scale backend-listener up to old value
    """

    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    response = prod_client.get("/")
    assert response.status_code == 200
    openshift.scale("backend-listener", 0)

    try:
        # Test if response will succeed on production calls
        for _ in range(3):
            response = prod_client.get("/", params=None)
            assert response.status_code == 200

        # Test if response will succeed on production call after failed one
        response = prod_client.get("/", params={"user_key": ":user_key"})
        assert response.status_code == 403
        response = prod_client.get("/", params=None)
        assert response.status_code == 200
    finally:
        openshift.scale("backend-listener", replicas)
