"""
Rewrite: 3scale-amp-tests/spec/functional_specs/update_staging_spec.rb
"""

import pytest

pytestmark = [pytest.mark.nopersistence]
# Test checks changes during test run hence is incompatible with persistence plugin


@pytest.fixture(scope="module")
def old_api_client(api_client):
    """Api client with default user_key"""
    return api_client()


@pytest.fixture(scope="module")
def new_api_client(api_client, service):
    """Api client with updated user_key"""
    # change of the user key
    service.proxy.list().update(params={"auth_user_key": "new_key"})
    service.proxy.deploy()

    return api_client()


def test_updated_auth_param(old_api_client, new_api_client):
    """
    The update of the staging configuration must be propagated immediately

    Request using the old key returns 403
    Request using the new_key returns 200
    """

    old_param_response = old_api_client.get("/anything")
    new_param_response = new_api_client.get("/anything")

    assert old_param_response.status_code == 403
    assert new_param_response.status_code == 200
