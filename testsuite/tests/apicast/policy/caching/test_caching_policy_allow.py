"""
Rewrite spec/functional_specs/policies/caching/caching_allow_policy_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability


@pytest.fixture(scope="module")
def policy_settings():
    "Add caching policy configured as 'caching_type': 'allow'"
    return rawobj.PolicyConfig("caching", {"caching_type": "allow"})


@pytest.mark.required_capabilities(Capability.SCALING)
def test_caching_policy_allow(prod_client, openshift, application):
    """
    Test caching policy with caching mode set to Allow

    To cache credentials:
        - make request to production gateway with valid credentials
        - make request to production gateway with invalid credentials
    Scale backend-listener down
    Test if:
        - response with valid credentials have status_code == 200
        - response with same invalid credentials as before have status_code == 403
        - response with new invalid credentials have status_code == 200
    Scale backend-listener up to old value
    """

    client = prod_client()
    client.auth = None
    auth = application.authobj()

    response = client.get("/", auth=auth)
    assert response.status_code == 200
    response = client.get("/", params={"user_key": ":user_key"})
    assert response.status_code == 403

    with openshift().scaler.scale("backend-listener", 0):
        # Test if response succeed on production calls with valid credentials
        for _ in range(3):
            response = client.get("/", auth=auth)
            assert response.status_code == 200

        # Test if response fail on production calls with known invalid credentials
        for _ in range(3):
            response = client.get("/", params={"user_key": ":user_key"})
            assert response.status_code == 403

        # Test if response succeed on production calls with unknown invalid credentials
        for _ in range(3):
            response = client.get("/", params={"user_key": ":123"})
            assert response.status_code == 200
