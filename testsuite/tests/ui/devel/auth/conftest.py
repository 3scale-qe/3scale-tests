"""Conftest for auth tests"""

import pytest

from testsuite import settings
from testsuite.ui.views.devel.login import LoginDevelView


@pytest.fixture(scope="module")
def custom_devel_auth0_login(browser, navigator, provider_account):
    """
    Login to Developer portal with specific account or credentials
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    :return: Login to Developer portal with custom credentials via Auth0
    """

    def _login(email, password):
        url = settings["threescale"]["devel"]["url"]
        browser.url = url
        page = navigator.open(LoginDevelView,
                              access_code=provider_account['site_access_code'])
        page.do_auth0_login(email, password)

    return _login


@pytest.fixture(scope="module")
def custom_devel_rhsso_login(browser, navigator, provider_account):
    """
    Login to Developer portal with specific account or credentials
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    :return: Login to Developer portal with custom credentials via RHSSO
    """

    def _login(name, password):
        url = settings["threescale"]["devel"]["url"]
        browser.url = url
        page = navigator.open(LoginDevelView,
                              access_code=provider_account['site_access_code'])
        page.do_rhsso_login(name, password)

    return _login
