"""Test for login into devel portal via Auth0"""
import pytest

from testsuite.ui.views.admin.audience.developer_portal.sso_integrations import Auth0IntegrationEditView, \
    Auth0IntegrationDetailView
from testsuite.ui.views.devel import SignUpView, BaseDevelView


@pytest.fixture(scope="module")
def auth0_integration(request, threescale, testconfig, custom_admin_login, navigator):
    """
    Due to the fact that once you create sso integration you can't delete it only edit it,
    this workaround is needed to simplify UI test
    """
    auth = [x for x in threescale.dev_portal_auth_providers.list() if x['kind'] == "auth0" in x]
    if not auth:
        auth = [threescale.dev_portal_auth_providers.create(
            {"kind": "auth0", "client_id": "tmp", "client_secret": "tmp", "site": "https://anything.invalid"})]

    if not testconfig["skip_cleanup"]:
        def _delete():
            custom_admin_login()
            sso_edit = navigator.navigate(Auth0IntegrationDetailView, integration=auth[0])
            sso_edit.publish_checkbox.check(False)

        request.addfinalizer(_delete)

    return auth[0]


@pytest.fixture(scope="module", autouse=True)
def auth0_setup(custom_admin_login, navigator, testconfig, set_callback_urls, auth0_integration):
    """Setup for Auth0 integration"""
    custom_admin_login()
    sso = navigator.navigate(Auth0IntegrationEditView, integration=auth0_integration)
    auth = testconfig["auth0"]
    sso.edit(auth["client"], auth["client-secret"], f"https://{auth['domain']}")

    sso = navigator.navigate(Auth0IntegrationDetailView, integration=auth0_integration)
    set_callback_urls(testconfig["auth0"]["client"], sso.callback_urls())
    sso.publish()


@pytest.mark.disruptive  # Only one instance of Auth0 could be present at the time so this test is disruptive to all
# other tests that want to setup Auth0 integration for devel portal
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7633")
def test_devel_login_auth0(custom_devel_auth0_login, navigator, auth0_user, auth0_user_password):
    """
    Test
        - Login into developer portal via Auth0
        - Assert that login was successful
    """
    custom_devel_auth0_login(auth0_user["email"], auth0_user_password)
    signup_view = SignUpView(navigator.browser)
    assert signup_view.wait_displayed()

    signup_view.signup("RedHat")

    devel_view = BaseDevelView(navigator.browser)
    assert devel_view.is_displayed
    assert devel_view.is_logged_in
