"""
Rewrite spec/functional_specs/policies/caching/caching_resilient_policy_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

pytestmark = pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)


@pytest.fixture(scope="module")
def policy_settings():
    "Add caching policy configured as 'caching_type': 'resilient'"
    return rawobj.PolicyConfig("caching", {"caching_type": "resilient"})


@pytest.mark.disruptive
# TODO: flaky because ocp4 won't scale the pod to 0, we need to use apimanager object to change replicas
@pytest.mark.flaky
def test_caching_policy_resilient(prod_client, openshift, application):
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

    client = prod_client()
    client.auth = None
    auth = application.authobj()

    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    response = client.get("/", auth=auth)
    assert response.status_code == 200
    openshift.scale("backend-listener", 0)

    try:
        # Test if response will succeed on production calls
        for _ in range(3):
            response = client.get("/", auth=auth)
            assert response.status_code == 200

        # Test if response will succeed on production call after failed one
        response = client.get("/", params={"user_key": ":user_key"})
        assert response.status_code == 403
        response = client.get("/", auth=auth)
        assert response.status_code == 200
    finally:
        openshift.scale("backend-listener", replicas)
