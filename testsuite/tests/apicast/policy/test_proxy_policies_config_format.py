"""
Test proxy policies config format
"""
import json

import pytest
from threescale_api.errors import ApiClientError

from testsuite import rawobj


pytestmark = pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-1059")


@pytest.fixture
def policy():
    """Returns valid policy."""
    return rawobj.PolicyConfig(
        "headers", {"response": [{"op": "set", "header": "X-FOO", "value_type": "plain", "value": "Bar"}]}
    )


@pytest.fixture
def invalid_policy():
    """Returns wrong format non-existent policy."""
    return {"name": "foo"}


@pytest.fixture(scope="module")
def proxy(service):
    """Returns proxy instance."""
    return service.proxy.list()


def test_send_invalid_policy(proxy, invalid_policy):
    """Send invalid policy to threescale should fails 422 Unprocessable Entity."""
    params = {
        "policies_config": invalid_policy,
        "service_id": proxy.service["id"],
    }
    with pytest.raises(ApiClientError) as error:
        proxy.policies.update(params=params)

    assert error.value.code == 422

    errors = json.loads(error.value.body)["policies_config"][0]["errors"]
    assert "version" in errors
    assert "configuration" in errors


def test_send_valid_policy(proxy, policy):
    """Send policy to threescale should works just fine."""
    response = proxy.policies.insert(0, policy)
    assert response["policies_config"][0]["name"] == policy["name"]
