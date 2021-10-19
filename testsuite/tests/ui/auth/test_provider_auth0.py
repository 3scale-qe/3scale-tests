"""
Rewrite of spec/ui_specs/oauth/provider_auth0_spec.rb
"""
import pytest

from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.settings.sso_integrations import SSOIntegrationDetailView
from testsuite.ui.views.auth import Auth0View


# pylint: disable=unused-argument, too-many-arguments
@pytest.mark.disruptive
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
