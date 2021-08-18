"""
Conftest for auth tests
"""
# pylint: disable=unused-argument, too-many-arguments
import pytest

from testsuite.ui.views.admin.settings.sso_integrations import NewSSOIntegrationView, SSOIntegrationEditView


@pytest.fixture(scope="module")
def ui_sso_integration(custom_admin_login, navigator, threescale, testconfig, request):
    """
    Create 3scale SSO integration via UI
    """

    def _sso_integration(sso_type: str, client: str, client_secret: str, realm: str):
        custom_admin_login()
        sso = navigator.navigate(NewSSOIntegrationView)
        sso_id = sso.create(sso_type, client, client_secret, realm)
        sso = threescale.admin_portal_auth_providers.read(sso_id)

        if not testconfig["skip_cleanup"]:
            def _delete():
                custom_admin_login()
                sso_edit = navigator.navigate(SSOIntegrationEditView, integration=sso)
                sso_edit.delete()

            request.addfinalizer(_delete)
        return sso

    return _sso_integration
