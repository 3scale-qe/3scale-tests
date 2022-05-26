"""
Conftest for auth tests
"""
# pylint: disable=unused-argument, too-many-arguments
import pytest

from testsuite import resilient
from testsuite.ui.views.admin.settings.sso_integrations import NewSSOIntegrationView, SSOIntegrationEditView, \
    SSOIntegrationDetailView
from testsuite.ui.views.auth import Auth0View, RhssoView


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


@pytest.fixture(scope="module")
def auth0_setup(custom_admin_login, testconfig, ui_sso_integration, navigator, set_callback_urls, auth0_user,
                threescale):
    """
    Preparation for Auth0 tests:
        - Crate Auth0 SSO integration
        - Set callback urls for Auth0 client
        - test authentication flow
        - publish SSO integration
    """
    custom_admin_login()
    auth = testconfig["auth0"]
    integration = ui_sso_integration('auth0', auth["client"], auth["client-secret"], f"https://{auth['domain']}")

    sso = navigator.navigate(SSOIntegrationDetailView, integration=integration)
    urls = sso.callback_urls()
    set_callback_urls(testconfig["auth0"]["client"], urls)

    sso.test_flow(Auth0View, auth0_user["email"], "RedHat123")
    assert sso.test_flow_checkbox.is_checked
    sso.publish()

    yield urls

    if not testconfig["skip_cleanup"]:
        name = auth0_user["email"].split("@")[0]
        user = resilient.resource_read_by_name(threescale.provider_account_users, name)
        user.delete()


@pytest.fixture
def auth0_login(auth0_setup, auth0_user, custom_auth0_login):
    """Login into 3scale via RHSSO"""
    custom_auth0_login(auth0_user["email"], "RedHat123", False)


@pytest.fixture
def auth0_bounce_login(auth0_setup, navigator, browser, auth0_user):
    """Login into 3scale via RHSSO using /bounce URL"""
    bounce_url = auth0_setup[0].replace("/callback", "/bounce")
    navigator.open(url=bounce_url)
    provider = Auth0View(browser.root_browser)
    provider.login(auth0_user["email"], "RedHat123")


# pylint: disable=too-many-locals
@pytest.fixture(scope="module")
def rhsso_setup(request, custom_admin_login, rhsso_service_info, ui_sso_integration, navigator, testconfig,
                threescale):
    """
    Preparation for RHSSO tests:
        - Crate RHSSO SSO integration
        - Set callback urls for RHSSO client
        - test authentication flow
        - publish SSO integration
    """
    custom_admin_login()
    admin = rhsso_service_info.realm.admin
    client_id = rhsso_service_info.client.client_id
    client = admin.get_client(client_id)["clientId"]
    client_secret = admin.get_client_secrets(client_id)["value"]
    integration = ui_sso_integration('keycloak', client, client_secret, rhsso_service_info.issuer_url())

    sso = navigator.navigate(SSOIntegrationDetailView, integration=integration)
    urls = sso.callback_urls()
    admin.update_client(client_id, payload={"standardFlowEnabled": True, "redirectUris": urls})

    test_user = testconfig["rhsso"]["test_user"]
    sso.test_flow(RhssoView, test_user["username"], test_user["password"])
    assert sso.test_flow_checkbox.is_checked
    sso.publish()

    def _delete():
        user = resilient.resource_read_by_name(threescale.provider_account_users,
                                               admin.get_user(rhsso_service_info.user)["username"])
        user.delete()

    request.addfinalizer(_delete)

    return urls


@pytest.fixture
def rhsso_login(rhsso_setup, testconfig, custom_rhsso_login, rhsso_service_info):
    """Login into 3scale via RHSSO"""
    test_user = testconfig["rhsso"]["test_user"]
    custom_rhsso_login(test_user["username"], test_user["password"])


@pytest.fixture()
def rhsso_bounce_login(rhsso_setup, navigator, testconfig, browser, rhsso_service_info, threescale):
    """Login into 3scale via RHSSO using /bounce URL"""
    bounce_url = rhsso_setup[0].replace("/callback", "/bounce")
    username = testconfig["rhsso"]["test_user"]["username"]
    user_id = rhsso_service_info.realm.admin.get_user_id(username)
    rhsso_service_info.realm.admin.user_logout(user_id)
    navigator.open(url=bounce_url)
    provider = RhssoView(browser.root_browser)
    test_user = testconfig["rhsso"]["test_user"]
    provider.login(test_user["username"], test_user["password"])
