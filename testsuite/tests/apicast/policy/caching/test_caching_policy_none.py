"""
Rewrite spec/functional_specs/policies/caching/caching_none_policy_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)


@pytest.fixture(scope="module")
def policy_settings():
    "Add caching policy configured as 'caching_type': 'none'"
    return rawobj.PolicyConfig("caching", {"caching_type": "none"})


@pytest.mark.disruptive
# TODO: flaky because ocp4 won't scale the pod to 0, we need to use apimanager object to change replicas
@pytest.mark.flaky
def test_caching_policy_none(prod_client, openshift):
    """
    Test caching policy with caching mode set to None

    Scale backend-listener down
    Test if:
        - all responses fail because 'caching type': 'none' disable caching
    Scale backend-listener up to old value
    """

    client = prod_client()
    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    response = client.get("/")
    assert response.status_code == 200
    openshift.scale("backend-listener", 0)

    # Test if responses will fail on production calls
    try:
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 403
    finally:
        openshift.scale("backend-listener", replicas)
