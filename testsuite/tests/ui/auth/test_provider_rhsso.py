"""
Rewrite of spec/ui_specs/oauth/provider_rhsso_spec.rb
"""
import pytest

from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.settings.sso_integrations import SSOIntegrationDetailView, RhssoView


# pylint: disable=unused-argument, too-many-arguments, too-many-locals
@pytest.mark.disruptive
def test_provider_rhsso(login, navigator, ui_sso_integration, rhsso_service_info, testconfig, custom_rhsso_login):
    """
    Preparation:
        - Crate RHSSO SSO integration
        - Set callback urls for RHSSO client
    Test:
        - authentication flow
        - publish SSO integration
        - login to 3scale via RHSSO
        - assert that you are logged in
    """
    admin = rhsso_service_info.realm.admin
    client_id = rhsso_service_info.client.client_id
    client = admin.get_client(client_id)["clientId"]
    client_secret = admin.get_client_secrets(client_id)["value"]
    integration = ui_sso_integration('keycloak', client, client_secret, rhsso_service_info.issuer_url())

    sso = navigator.navigate(SSOIntegrationDetailView, integration=integration)
    urls = sso.callback_urls()
    admin.update_client(client_id, payload={"standardFlowEnabled": True, "redirectUris": urls})

    test_user = testconfig["rhsso"]["test_user"]
    username = test_user["username"]
    password = test_user["password"]
    sso.test_flow(RhssoView, username, password)
    sso.publish()

    custom_rhsso_login(username, password, admin.get_user(rhsso_service_info.user)["username"])
    admin_view = navigator.navigate(BaseAdminView)
    assert admin_view.is_displayed
