"UI conftest"

import pytest

from testsuite.config import settings
from testsuite.ui.webdriver import SeleniumDriver
from testsuite.ui.browser import ThreeScaleBrowser
from testsuite.ui.navigation import Navigator
from testsuite.ui.views.admin import BaseAdminView, LoginView


@pytest.fixture(scope="session")
def browser(custom_browser):
    """
       Browser representation based on UI settings
       Args:
           :param custom_browser: custom browser function
           :return browser instance
    """
    return custom_browser()


@pytest.fixture(scope="session")
def custom_browser(request):
    """
        Browser representation based on UI settings
        Args:
            :param request: finalizer for browser teardown
    """
    def _custom_browser(url=None):
        """
        :param url: url which should be used for browser navigation and usage
        :return: browser instance
        """
        webdriver = SeleniumDriver(provider=settings["fixtures"]["ui"]["browser"]["provider"],
                                   driver=settings["fixtures"]["ui"]["browser"]["webdriver"],
                                   ssl_verify=settings["ssl_verify"])
        webdriver.get_driver()
        started_browser = ThreeScaleBrowser(selenium=webdriver.webdriver)
        started_browser.url = url or settings["threescale"]["admin"]["url"]
        request.addfinalizer(webdriver.finalize)
        return started_browser

    return _custom_browser


@pytest.fixture(scope="function")
def custom_login(browser, request):
    """
       Method for basic login to 3scale tenant
       :param browser: browser based on UI settings
       :param request: finalizer for session cleanup
       :return: Logged browser
    """
    def _login(name=None, password=None):
        def _clear_session():
            browser.selenium.delete_all_cookies()
            browser.url = settings["threescale"]["admin"]["url"]

        login = LoginView(browser)
        login.do_login(name or settings["ui"]["username"], password or settings["ui"]["password"])
        request.addfinalizer(_clear_session)
        return browser

    return _login


@pytest.fixture(scope="function")
def login(custom_login):
    """
    Default login method called with test on start
    :param custom_login: Parametrized login method
    :return: Login with default credentials
    """
    return custom_login()


@pytest.fixture(scope="function")
def navigator(browser):
    """
        Navigator for 3scale UI pages/Views
        :param browser: browser based on UI settings
        :return: Navigator instance
    """
    base_views = [
        BaseAdminView
    ]
    navigator = Navigator(browser, base_views)
    return navigator
