"""
rewritten the /spec/functional_specs/custom_tenant_spec.rb
Creates a new tenant and tests if the tenant works
"""
import pytest

from testsuite import rawobj, resilient
from testsuite.utils import blame


@pytest.fixture(scope="session")
def threescale(custom_tenant, testconfig):
    """
    Creates a new tenant and returns a threescale client configured to use
    the new tenant
    """
    tenant = custom_tenant()
    # This has to wait, backoff is not an option as this can create an object
    # despite to returned error (would keep trash there), the wait time has to
    # be really long.
    return tenant.admin_api(ssl_verify=testconfig["ssl_verify"], wait=0)


@pytest.fixture(scope="module")
def account(custom_account, request, account_password):
    """Local module scoped account to utilize custom tenant"""
    iname = blame(request, "id")
    account = rawobj.Account(org_name=iname, monthly_billing_enabled=None, monthly_charging_enabled=None)
    account.update(
        {
            "name": iname,
            "username": iname,
            "email": f"{iname}@example.com",
            "password": account_password,
        }
    )
    account = custom_account(params=account)

    return account


@pytest.fixture(scope="module")
def custom_account(threescale, request, testconfig):
    """Local module scoped custom_account to utilize custom tenant

    Args:
        :param params: dict for remote call, rawobj.Account should be used
    """

    def _custom_account(params, autoclean=True, threescale_client=threescale):
        acc = resilient.accounts_create(threescale_client, params=params)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(acc.delete)
        return acc

    return _custom_account


# FIXME: threescale_api.errors.ApiClientError: Response(422): b'{"errors":{"system_name":["must be shorter."]}}
# Name of the tenant is too long
def test_custom_tenant(api_client):
    """
    Makes a request using the tenant
    Asserts that the response code is 200
    """
    response = api_client().get("/anything")
    assert response.status_code == 200
