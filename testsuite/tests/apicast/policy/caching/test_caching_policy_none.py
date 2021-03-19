"""
Rewrite spec/functional_specs/policies/caching/caching_none_policy_spec.rb
"""
import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    "Add caching policy configured as 'caching_type': 'none'"
    return rawobj.PolicyConfig("caching", {"caching_type": "none"})


def test_caching_policy_none(prod_client, openshift):
    """
    Test caching policy with caching mode set to None

    Scale backend-listener down
    Test if:
        - all responses fail because 'caching type': 'none' disable caching
    Scale backend-listener up to old value
    """

    client = prod_client()
    response = client.get("/")
    assert response.status_code == 200

    # Test if responses will fail on production calls
    with openshift().scaler.scale("backend-listener", 0):
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 403
