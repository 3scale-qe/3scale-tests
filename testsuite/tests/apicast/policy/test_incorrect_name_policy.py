"""
Rewrite spec/functional_specs/policies/incorrect_policy_name_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability


@pytest.fixture(scope="module")
def policy_settings():
    """Configure 'incorrect_name' policy which is non-existing/invalid"""

    return rawobj.PolicyConfig("incorrect_name", {"rules": []})


def test_incorrect_name_policy_staging_call(api_client):
    """Calls through staging gateway should be still working"""

    response = api_client().get("/get")
    assert response.status_code == 200


@pytest.mark.disruptive
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)
def test_incorrect_name_policy_production_call(prod_client):
    """Calls through production gateway should be still working"""

    response = prod_client().get("/get")
    assert response.status_code == 200
