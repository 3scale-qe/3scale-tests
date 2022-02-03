"""
rewritten the /spec/functional_specs/custom_tenant_spec.rb
Creates a new tenant and tests if the tenant works
"""
import pytest


@pytest.fixture(scope="session")
def threescale(custom_tenant, testconfig):
    """
    Creates a new tenant and returns a threescale client configured to use
    the new tenant
    """
    tenant = custom_tenant()
    return tenant.admin_api(ssl_verify=testconfig["ssl_verify"], wait=32)


# FIXME: threescale_api.errors.ApiClientError: Response(422): b'{"errors":{"system_name":["must be shorter."]}}
# Name of the tenant is too long
@pytest.mark.flaky
def test_custom_tenant(api_client):
    """
    Makes a request using the tenant
    Asserts that the response code is 200
    """
    response = api_client().get("/anything")
    assert response.status_code == 200
