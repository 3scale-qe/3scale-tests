"""
rewritten the /spec/functional_specs/custom_tenant_spec.rb
Creates a new tenant and tests if the tenant works
"""
import backoff
import pytest
from threescale_api import client
from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(scope="session")
def threescale(testconfig, master_threescale, request):
    """
    Creates a new tenant and returns a threescale client configured to use
    the new tenant
    """
    tenant = master_threescale.tenants.create(rawobj.CustomTennant(
        username=blame(request, "t")))

    url = "https://" + tenant.entity["signup"]["account"]["admin_domain"]
    access_token = tenant.entity["signup"]["access_token"]["value"]

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(tenant.delete)

    verify = testconfig["ssl_verify"]
    return get_custom_client(url, access_token, verify)


@backoff.on_predicate(backoff.constant, lambda x: not x.account_plans.exists() or
                      len(x.account_plans.fetch()["plans"]) < 1, interval=5, max_time=60)
def get_custom_client(url, access_token, ssl_verify):
    """
    Given the credentials, returns a client for the custom tenant.
    Retries until an account plan is created. When that object exists, tenant is ready.
    When fetching account plans without previous check if they have been created
    503 error can be returned
    """
    return client.ThreeScaleClient(url=url, token=access_token, ssl_verify=ssl_verify)


def test_custom_tenant(api_client):
    """
    Makes a request using the tenant
    Asserts that the response code is 200
    """
    response = api_client.get("/anything")
    assert response.status_code == 200
