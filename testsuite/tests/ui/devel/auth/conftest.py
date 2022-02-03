"""Conftest for auth tests"""

import pytest

from testsuite import settings
from testsuite.ui.views.devel.login import LoginDevelView


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def custom_devel_auth0_login(browser, navigator, provider_account, threescale, testconfig):
    """
    Login to Developer portal with specific account or credentials
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    :param threescale: 3scale API client
    :param request: We need this to be able to delete automatic created user after tests.
    :return: Login to Developer portal with custom credentials via Auth0
    """
    cleanup = []

    def _login(email, password):
        browser.selenium.delete_all_cookies()
        url = settings["threescale"]["devel"]["url"]
        browser.url = url
        page = navigator.open(LoginDevelView,
                              access_code=provider_account['site_access_code'])
        page.do_auth0_login(email, password)
        cleanup.append(email)

    yield _login

    if not testconfig["skip_cleanup"]:
        for email in cleanup:
            name = email.split("@")[0]
            account = [x for x in threescale.accounts.list() if x.users.list()[0]['username'] == name][0]
            account.delete()


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def custom_devel_rhsso_login(browser, navigator, provider_account, threescale, testconfig):
    """
    Login to Developer portal with specific account or credentials
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    :return: Login to Developer portal with custom credentials via RHSSO
    """
    cleanup = []

    def _login(name, password, rhsso_username):
        browser.selenium.delete_all_cookies()
        url = settings["threescale"]["devel"]["url"]
        browser.url = url
        page = navigator.open(LoginDevelView,
                              access_code=provider_account['site_access_code'])
        page.do_rhsso_login(name, password)
        cleanup.append(rhsso_username)

    yield _login

    if not testconfig["skip_cleanup"]:
        for username in cleanup:
            account = [x for x in threescale.accounts.list() if x.users.list()[0]['username'] == username][0]
            account.delete()
