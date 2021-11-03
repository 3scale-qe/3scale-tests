"""
Tests for combination of token scopes
"""

import pytest

from testsuite.ui.views.admin.settings.tokens import Scopes, TokenNewView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def token(custom_admin_login, navigator, request, threescale, permission):
    """
    Create token with all scopes
    """
    custom_admin_login()
    new = navigator.navigate(TokenNewView)
    name = blame(request, "token")

    def _delete():
        token = [x["name"] == name for x in threescale.access_tokens.list()][0]
        threescale.access_tokens.delete(token.entity_id)

    request.addfinalizer(_delete)
    token = new.create(name,
                       [Scopes.BILLING.value, Scopes.MANAGEMENT.value, Scopes.POLICY.value, Scopes.ANALYTICS.value],
                       permission[0])

    return token


def test_read_service(token, api_client):
    """
    Request to get list of services should have status code 200
    """

    response = api_client("GET", '/admin/api/services', token)
    assert response.status_code == 200


def test_create_account_user(account, token, api_client, request, permission):
    """
    Request to create user should have status code 403 (201 for write permission)
    """

    name = blame(request, "acc")
    params = {"account_id": account.entity_id, "username": name, "email": f"{name}@anything.invalid",
              "password": "123456"}
    response = api_client("POST", f"/admin/api/accounts/{account.entity_id}/users", token, params)
    assert response.status_code == permission[1]


def test_get_service_top_applications(service, token, api_client):
    """
    Request to get top applications should have status code 200
    """

    params = {"service_id": service.entity_id, "since": "2012-02-22 00:00:00", "period": "year", "metric_name": "hits"}
    response = api_client("GET", f"/stats/services/{service.entity_id}/top_applications", token, params)
    assert response.status_code == 200


def test_get_invoice_list(account, token, api_client):
    """
    Request to get list of invoices should have status code 200
    """

    params = {"account_id": account.entity_id}
    response = api_client("GET", f"/api/accounts/{account.entity_id}/invoices", token, params)
    assert response.status_code == 200


def test_create_invoice_line_item(invoice, token, api_client, request, permission):
    """
    Request to create line item should have status code 403 (201 for write permission)
    """

    name = blame(request, "item")
    params = {"invoice_id": invoice.entity_id, "name": name, "description": "description", "quantity": '1', "cost": 1}
    response = api_client("POST", f"/api/invoices/{invoice.entity_id}/line_items", token, json=params)
    assert response.status_code == permission[1]


def test_get_registry_policies_list(token, api_client):
    """
    Request to get list of registry policies should have status code 200
    """

    response = api_client("GET", "/admin/api/registry/policies", token)
    assert response.status_code == 200


# pylint: disable=too-many-arguments
def test_create_registry_policy(token, api_client, schema, permission, threescale, request):
    """
    Request to create policy registry should have status code 403 (201 for write permission)
    """
    params = {"name": "policy_registry", "version": "0.1", "schema": schema}
    response = api_client("POST", "/admin/api/registry/policies", token, json=params)
    if permission[0]:
        request.addfinalizer(lambda: threescale.policy_registry.delete("policy_registry-0.1"))
    assert response.status_code == permission[1]
