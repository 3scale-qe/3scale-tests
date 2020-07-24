"""
Rewrite spec/functional_specs/policies/caching/caching_strict_policy_spec.rb
"""

import time

import pytest

from testsuite import rawobj
from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)


@pytest.fixture(scope="module")
def policy_settings():
    "Add caching policy configured as 'caching_type': 'strict'"
    return rawobj.PolicyConfig("caching", {"caching_type": "strict"})


@pytest.mark.disruptive
# TODO: flaky because ocp4 won't scale the pod to 0, we need to use apimanager object to change replicas
@pytest.mark.flaky
def test_caching_policy_strict(prod_client, openshift):
    """
    Test caching policy with caching mode set to Strict

    To cache credentials:
        - make request to production gateway with valid credentials
    Scale backend-listener down
    Test if:
        - response with valid credentials have status_code == 200
        - after a successful response all the following responses will have status code 403
    Scale backend-listener up to old value
    """

    client = prod_client(version=2)
    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    response = client.get("/")
    assert response.status_code == 200
    openshift.scale("backend-listener", 0)

    # Test if requests start failing on production calls after first successful request
    try:
        response = client.get("/")
        assert response.status_code == 200
        status_code1 = 0
        status_code2 = 0
        timeout = time.time() + 40
        while time.time() < timeout:
            response1 = client.get("/")
            status_code1 = response1.status_code
            response2 = client.get("/")
            status_code2 = response2.status_code
            if status_code1 == 403 and status_code2 == 403:
                break
            time.sleep(5)
    finally:
        openshift.scale("backend-listener", replicas)

    assert status_code1 == 403
    assert status_code2 == 403
