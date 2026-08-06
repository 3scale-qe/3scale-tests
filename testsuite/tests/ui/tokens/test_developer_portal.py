"""
Test for Developer Portal API scope
"""

import pytest
from threescale_api.errors import ApiClientError

from testsuite.ui.views.admin.settings.tokens import Scopes, TokenNewView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def token(custom_admin_login, navigator, request, threescale, permission):
    """
    Create token with scope set to 'Developer Portal'
    """
    custom_admin_login()
    new = navigator.navigate(TokenNewView)
    name = blame(request, "token")
    token = new.create(name, [Scopes.DEVELOPER_PORTAL.value], permission[0])

    def _delete():
        token = list(filter(lambda x: x["name"] == name, threescale.access_tokens.list()))[0]
        threescale.access_tokens.delete(token.entity_id)

    request.addfinalizer(_delete)
    return token


def test_read_service(token, api_client):
    """
    Request to get list of services should have status code 403
    """

    response = api_client("GET", "/admin/api/services", token)
    assert response.status_code == 403


def test_create_account_user(account, token, api_client, request):
    """
    Request to create user should have status code 403
    """

    name = blame(request, "acc")
    params = {
        "account_id": account.entity_id,
        "username": name,
        "email": f"{name}@anything.invalid",
        "password": "123456",
    }
    response = api_client("POST", f"/admin/api/accounts/{account.entity_id}/users", token, params)
    assert response.status_code == 403


def test_get_service_top_applications(service, token, api_client):
    """
    Request to get top applications should have status code 403
    """

    params = {"service_id": service.entity_id, "since": "2012-02-22 00:00:00", "period": "year", "metric_name": "hits"}
    response = api_client("GET", f"/stats/services/{service.entity_id}/top_applications", token, params)
    assert response.status_code == 403


def test_get_invoice_list(account, token, api_client):
    """
    Request to get list of invoices should have status code 403
    """

    params = {"account_id": account.entity_id}
    response = api_client("GET", f"/api/accounts/{account.entity_id}/invoices", token, params)
    assert response.status_code == 403


def test_create_invoice_line_item(invoice, token, api_client, request):
    """
    Request to create line item should have status code 403
    """

    name = blame(request, "item")
    params = {"invoice_id": invoice.entity_id, "name": name, "description": "description", "quantity": "1", "cost": 1}
    response = api_client("POST", f"/api/invoices/{invoice.entity_id}/line_items", token, json=params)
    assert response.status_code == 403


def test_get_registry_policies_list(token, api_client):
    """
    Request to get list of registry policies should have status code 403
    """

    response = api_client("GET", "/admin/api/registry/policies", token)
    assert response.status_code == 403


def test_create_registry_policy(token, api_client, schema):
    """
    Request to create policy registry should have status code 403
    """
    params = {"name": "policy_registry", "version": "0.1", "schema": schema}
    response = api_client("POST", "/admin/api/registry/policies", token, json=params)
    assert response.status_code == 403


def test_create_provider_account(request, token, api_client):
    """
    Request to create provider account should have status code 403
    """
    username = blame(request, "username")
    params = {"username": username, "email": f"{username}@example.com", "password": "account_password"}
    response = api_client("POST", "/admin/api/users", token, params)
    assert response.status_code == 403


def test_create_app_key(token, api_client, account, application):
    """
    Request to create application key should have status code 403
    """
    account_id = account.entity_id
    application_id = application.entity_id
    params = {"account_id": account_id, "application_id": application_id, "key": "test_key"}
    response = api_client("POST", f"/admin/api/accounts/{account_id}/applications/{application_id}/keys", token, params)
    assert response.status_code == 403


def test_get_cms_templates(token, api_client):
    """
    Request to get CMS templates. Should have status code 200.
    """

    response = api_client("GET", "/admin/api/cms/templates", token)
    assert response.status_code == 200


def test_get_cms_sections(token, api_client):
    """
    Request to get CMS sections. Should have status code 200.
    """

    response = api_client("GET", "/admin/api/cms/sections", token)
    assert response.status_code == 200


def test_get_cms_files(token, api_client):
    """
    Request to get CMS files. Should have status code 200.
    """

    response = api_client("GET", "/admin/api/cms/files", token)
    assert response.status_code == 200


def test_create_cms_section(token, api_client, request, permission):
    """POST CMS section - 201 (write) or 403 (read-only)"""
    title = blame(request, "section")
    params = {"title": title, "public": True, "partial_path": f"/{title}"}
    response = api_client("POST", "/admin/api/cms/sections", token, json=params)
    assert response.status_code == permission[1]


def test_delete_cms_section(token, api_client, request, permission, threescale):
    """Create a new CMS section, then DELETE. 200 (write) or 403 (read-only)"""
    name = blame(request, "section")
    section = threescale.cms_sections.create({"title": name, "public": True, "partial_path": f"/{name}"})
    section_id = section["id"]

    response = api_client("DELETE", f"/admin/api/cms/sections/{section_id}", token)
    if permission[0]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403

    try:
        threescale.policy_registry.delete(section_id)
    except ApiClientError as e:
        if e.code != 404:
            raise
