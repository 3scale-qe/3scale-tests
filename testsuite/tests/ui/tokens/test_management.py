"""
Tests verifying that an access token scoped to 'Management' can access
service and account management endpoints but is denied access to analytics,
billing, CMS, and policy registry endpoints.
"""

import pytest
from threescale_api.errors import ApiClientError

from testsuite.ui.views.admin.settings.tokens import Scopes, TokenNewView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def token(custom_admin_login, navigator, request, threescale, permission):
    """
    Log in as admin, navigate to Settings > Tokens > New, and create an access
    token with scope set to 'Management' and the given permission level.
    """
    custom_admin_login()
    new = navigator.navigate(TokenNewView)
    name = blame(request, "token")
    token = new.create(name, [Scopes.MANAGEMENT.value], permission[0])

    def _delete():
        token = list(filter(lambda x: x["name"] == name, threescale.access_tokens.list()))[0]
        threescale.access_tokens.delete(token.entity_id)

    request.addfinalizer(_delete)
    return token


def test_read_service(token, api_client):
    """
    Using a Management-scoped token, send a GET request to /admin/api/services.
    Verify the response is 200 OK.
    """

    response = api_client("GET", "/admin/api/services", token)
    assert response.status_code == 200


# pylint: disable=too-many-arguments
def test_create_account_user(account, token, api_client, request, permission, account_password):
    """
    Using a Management-scoped token, send a POST request to create a new user
    under an existing account. Verify the response is 201 Created (write) or 403 Forbidden (read-only).
    """

    name = blame(request, "acc")
    params = {
        "account_id": account.entity_id,
        "username": name,
        "email": f"{name}@anything.invalid",
        "password": account_password,
    }
    response = api_client("POST", f"/admin/api/accounts/{account.entity_id}/users", token, params)
    assert response.status_code == permission[1]


def test_get_service_top_applications(service, token, api_client):
    """
    Using a Management-scoped token, send a GET request for a service's top
    applications statistics. Verify the response is 403 Forbidden.
    """

    params = {"service_id": service.entity_id, "since": "2012-02-22 00:00:00", "period": "year", "metric_name": "hits"}
    response = api_client("GET", f"/stats/services/{service.entity_id}/top_applications", token, params)
    assert response.status_code == 403


@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-761")
def test_get_invoice_list(account, token, api_client):
    """
    Using a Management-scoped token, send a GET request for an account's
    invoices. Verify the response is 403 Forbidden.
    """

    params = {"account_id": account.entity_id}
    response = api_client("GET", f"/api/accounts/{account.entity_id}/invoices", token, params)
    assert response.status_code == 403


@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-761")
def test_create_invoice_line_item(invoice, token, api_client, request):
    """
    Using a Management-scoped token, send a POST request to create a line item on
    an existing invoice. Verify the response is 403 Forbidden.
    """

    name = blame(request, "item")
    params = {"invoice_id": invoice.entity_id, "name": name, "description": "description", "quantity": "1", "cost": 1}
    response = api_client("POST", f"/api/invoices/{invoice.entity_id}/line_items", token, json=params)
    assert response.status_code == 403


def test_get_registry_policies_list(token, api_client):
    """
    Using a Management-scoped token, send a GET request to list registry
    policies. Verify the response is 403 Forbidden.
    """

    response = api_client("GET", "/admin/api/registry/policies", token)
    assert response.status_code == 403


def test_create_registry_policy(token, api_client, schema):
    """
    Using a Management-scoped token, send a POST request to create a new
    policy registry entry. Verify the response is 403 Forbidden.
    """
    params = {"name": "policy_registry", "version": "0.1", "schema": schema}
    response = api_client("POST", "/admin/api/registry/policies", token, json=params)
    assert response.status_code == 403


# pylint: disable=too-many-arguments
def test_create_provider_account(request, token, api_client, permission, threescale, account_password):
    """
    Using a Management-scoped token, send a POST request to create a new
    provider account user. Verify the response is 201 Created (write) or 403 Forbidden (read-only).
    """
    username = blame(request, "username")
    params = {"username": username, "email": f"{username}@example.com", "password": account_password}
    response = api_client("POST", "/admin/api/users", token, params)
    if permission[0]:
        request.addfinalizer(lambda: threescale.provider_account_users.delete(response.json()["user"]["id"]))
    assert response.status_code == permission[1]


def test_create_app_key(token, api_client, account, application, permission):
    """
    Using a Management-scoped token, send a POST request to create an
    application key for an existing account's application. Verify the response is
    201 Created (write) or 403 Forbidden (read-only).
    """
    account_id = account.entity_id
    application_id = application.entity_id
    params = {"account_id": account_id, "application_id": application_id, "key": "test_key"}
    response = api_client("POST", f"/admin/api/accounts/{account_id}/applications/{application_id}/keys", token, params)
    assert response.status_code == permission[1]


@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-761")
@pytest.mark.parametrize("resource", ["templates", "sections", "files"])
def test_get_cms_resource(token, api_client, resource):
    """
    Using a Management-scoped token, send a GET request to list a CMS resource.
    Verify the response is 403 Forbidden.
    """

    response = api_client("GET", f"/admin/api/cms/{resource}", token)
    assert response.status_code == 403


@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-761")
def test_create_cms_section(token, api_client, request):
    """
    Using a Management-scoped token, send a POST request to create a new CMS
    section. Verify the response is 403 Forbidden.
    """
    title = blame(request, "section")
    params = {"title": title, "public": True, "partial_path": f"/{title}"}
    response = api_client("POST", "/admin/api/cms/sections", token, json=params)
    assert response.status_code == 403


def test_delete_service(custom_service, token, api_client, permission, request):
    """
    Create a service via the API, then using a Management-scoped token, send a
    DELETE request to remove it. Verify the response is 200 OK (write) or
    403 Forbidden (read-only).
    """
    service = custom_service({"name": blame(request, "svc_delete")}, autoclean=False)
    response = api_client("DELETE", f"/admin/api/services/{service.entity_id}", token)

    if permission[0]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403

    try:
        service.delete()
    except ApiClientError as e:
        if e.code != 404:
            raise
