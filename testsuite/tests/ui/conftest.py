"UI conftest"

import pytest
from threescale_api.resources import Account

from testsuite.config import settings
from testsuite.ui.views.admin.audience.application import ApplicationNewView
from testsuite.ui.webdriver import SeleniumDriver
from testsuite.ui.browser import ThreeScaleBrowser
from testsuite.ui.navigation import Navigator
from testsuite.ui.views.admin import BaseAdminView, LoginView, AccountNewView
from testsuite.utils import blame


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
                                   ssl_verify=settings["ssl_verify"],
                                   remote_url=settings["fixtures"]["ui"]["browser"]["remote_url"]
                                   )
        webdriver.get_driver()
        started_browser = ThreeScaleBrowser(selenium=webdriver.webdriver)
        started_browser.url = url or settings["threescale"]["admin"]["url"]
        request.addfinalizer(webdriver.finalize)
        return started_browser

    return _custom_browser


@pytest.fixture(scope="module")
def custom_login(browser, request):
    """
       Method for basic login to 3scale tenant, fixture finalizer scope can be overridden by finalizer_request
       :param browser: browser based on UI settings
       :param request: finalizer for session cleanup
       :return: Function with logged browser
    """

    def _login(name=None, password=None, finalizer_request=None):
        finalizer_request = finalizer_request or request

        def _clear_session():
            browser.selenium.delete_all_cookies()
            if old_session:
                browser.selenium.add_cookie(old_session)
                browser.refresh()

        old_session = browser.selenium.get_cookie('user_session')
        browser.selenium.delete_all_cookies()
        browser.url = settings["threescale"]["admin"]["url"]
        login = LoginView(browser)
        login.do_login(name or settings["ui"]["username"], password or settings["ui"]["password"])
        finalizer_request.addfinalizer(_clear_session)
        return browser

    return _login


@pytest.fixture(scope="module")
def login(custom_login):
    """
    Default login method called with test on start
    :param custom_login: Parametrized login method
    :return: Login with default credentials
    """
    return custom_login()


@pytest.fixture(scope="module")
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


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def custom_ui_account(login, navigator, threescale, request, testconfig):
    """
    Create a custom account
    """

    def _custom_account(name: str, email: str, password: str, org_name: str, autoclean=True):
        account = navigator.navigate(AccountNewView)
        account.create(name, email, password, org_name)
        account = threescale.accounts.read_by_name(name)

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(account.delete)
        return account

    return _custom_account


@pytest.fixture(scope="module")
def ui_account(custom_ui_account, request):
    """Create an account through UI"""
    name = blame(request, "ui_account")
    return custom_ui_account(name, f"{name}@anything.invalid", name, name)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def custom_ui_application(login, navigator, threescale, request, testconfig):
    """
    :return: params for custom application
    """

    def _custom_ui_appliaction(name: str, email: str, account: Account, autoclean=True):
        app = navigator.navigate(ApplicationNewView, account_id=account.entity_id)
        app.create(name, email)
        application = account.applications.read_by_name(name)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(application.delete)
        return application

    return _custom_ui_appliaction


@pytest.fixture(scope="module")
def ui_application(custom_ui_application, account, request):
    """Create an application through UI"""
    name = blame(request, "ui_account")
    return custom_ui_application(name, f"{name}@anything.invalid", account)
