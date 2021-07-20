"""
Rewrite of spec/ui_specs/oauth/provider_auth0_spec.rb
"""

import pytest
from auth0.v3.management import auth0

from testsuite.auth0 import auth0_token
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.settings.sso_integrations import SSOIntegrationDetailView, Auth0View
from testsuite.utils import blame


@pytest.fixture(scope="module")
def auth0_client(testconfig):
    """
    API client for Auth0
    """
    return auth0.Auth0(testconfig["auth0"]["domain"], auth0_token())


@pytest.fixture(scope="module")
def set_callback_urls(auth0_client):
    """
    Set callback urls for Auth0 application
    """

    def _set_callback_urls(client_id, urls: list):
        auth0_client.clients.update(client_id, body={"callbacks": urls})

    return _set_callback_urls


@pytest.fixture
def auth0_user(auth0_client, request, testconfig):
    """
    Create Auth0 user via Auth0 API
    """
    name = blame(request, "auth_user")
    user = auth0_client.users.create({"email": f"{name}@anything.invalid", "password": "RedHat123",
                                      "connection": "Username-Password-Authentication", "email_verified": True})
    if not testconfig["skip_cleanup"]:
        def _delete():
            auth0_client.users.delete(user["user_id"])

        request.addfinalizer(_delete)
    return user


# pylint: disable=unused-argument, too-many-arguments
def test_provider_auth0(login, navigator, ui_sso_integration, testconfig, auth0_user, set_callback_urls,
                        custom_auth0_login):
    """
    Preparation:
        - Crate Auth0 SSO integration
        - Set callback urls for Auth0 application
    Test:
        - authentication flow
        - publish SSO integration
        - login to 3scale via Auth0
        - assert that you are logged in
    """
    auth = testconfig["auth0"]
    integration = ui_sso_integration('auth0', auth["client"], auth["client-secret"], f"https://{auth['domain']}")

    sso = navigator.navigate(SSOIntegrationDetailView, integration=integration)
    set_callback_urls(testconfig["auth0"]["client"], sso.callback_urls())

    email = auth0_user["email"]
    password = "RedHat123"
    sso.test_flow(Auth0View, email, password)
    sso.publish()

    custom_auth0_login(email, password)
    admin_view = navigator.navigate(BaseAdminView)
    assert admin_view.is_displayed
