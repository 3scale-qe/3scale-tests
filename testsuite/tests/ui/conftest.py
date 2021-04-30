"UI conftest"

import os
import pytest
from threescale_api.resources import Account, ApplicationPlan

from testsuite import rawobj
from testsuite.config import settings
from testsuite.tests.ui import Sessions
from testsuite.ui.browser import ThreeScaleBrowser
from testsuite.ui.navigation import Navigator
from testsuite.ui.views.admin.audience.account import AccountNewView
from testsuite.ui.views.admin.audience.application import ApplicationNewView
from testsuite.ui.views.admin.backend.backend import BackendNewView
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.login import LoginView
from testsuite.ui.views.admin.product.product import ProductNewView
from testsuite.ui.views.devel.login import LoginDevelView
from testsuite.ui.webdriver import SeleniumDriver
from testsuite.utils import blame


@pytest.fixture(scope="session")
def browser(request):
    """
    Browser representation based on UI settings
    Args:
        :param request: Finalizer for session cleanup
        :return browser: Browser instance
    """
    webdriver = SeleniumDriver(source=settings["fixtures"]["ui"]["browser"]["source"],
                               driver=settings["fixtures"]["ui"]["browser"]["webdriver"],
                               ssl_verify=settings["ssl_verify"],
                               remote_url=settings["fixtures"]["ui"]["browser"]["remote_url"],
                               binary_path=settings["fixtures"]["ui"]["browser"]["binary_path"])
    webdriver.get_driver()
    webdriver.post_init()
    started_browser = ThreeScaleBrowser(selenium=webdriver.webdriver)
    request.addfinalizer(webdriver.finalize)
    return started_browser


@pytest.fixture(scope="session")
def sessions(browser):
    """Sessions that were stored during test run"""
    return Sessions(browser)


@pytest.fixture(scope="module")
def custom_admin_login(browser, sessions, navigator):
    """
    Login fixture for admin portal.
    :param browser: Browser instance
    :param sessions: Dict-like instance that contains all available browserSessions that were used within scope=session
    :param navigator: Navigator Instance
    :return: Login to Admin portal with custom credentials
    """

    def _login(name=None, password=None):
        url = settings["threescale"]["admin"]["url"]
        name = name or settings["ui"]["username"]
        password = password or settings["ui"]["password"]
        browser.url = url

        if not sessions.restore(name, password, url):
            page = navigator.open(LoginView)
            page.do_login(name, password)
            cookies = [browser.selenium.get_cookie('user_session')]
            sessions.save(name, password, url, values=cookies)

    return _login


@pytest.fixture
def login(custom_admin_login):
    """
    Login to the Admin portal with default admin credentials
    :param custom_admin_login: Parametrized login method
    :return: Login with default credentials
    """
    return custom_admin_login()


@pytest.fixture(scope="module")
def custom_devel_login(browser, sessions, navigator, provider_account, account_password):
    """
    Login to Developer portal with specific account or credentials
    :param browser: Browser instance
    :param sessions: Dict-like instance that contains all available browserSessions that were used within scope=session
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    :param account_password: fixture that returns default account password
    :return: Login to Developer portal with custom credentials (account or name-password pair)
    """
    def _login(account=None, name=None, password=None):
        url = settings["threescale"]["devel"]["url"]
        name = name or account['org_name']
        password = password or account_password
        browser.url = url

        if not sessions.restore(name, password, url):
            page = navigator.open(LoginDevelView,
                                  access_code=provider_account['site_access_code'])
            page.do_login(name, password)
            cookies = [browser.selenium.get_cookie('access_code'),
                       browser.selenium.get_cookie('user_session')]
            sessions.save(name, password, url, values=cookies)

    return _login


@pytest.fixture
def devel_login(account, custom_devel_login):
    """
    return custom_admin_login()
    Login to the Developer portal with new account
    :param account: Source of login credentials
    :param custom_devel_login: Parametrized developer portal login method
    :return: Login to Developer portal with account created by session scoped fixture
    """
    return custom_devel_login(account=account)


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


# pylint: disable=unused-argument, too-many-arguments
@pytest.fixture(scope="module")
def custom_ui_backend(custom_admin_login, navigator, threescale, testconfig, request, private_base_url):
    """Parametrized custom Backend created via UI"""

    def _custom_ui_backend(name: str, system_name: str, description: str = "", endpoint: str = "", autoclean=True):
        custom_admin_login()
        if not endpoint:
            endpoint = private_base_url()

        backend = navigator.navigate(BackendNewView)
        backend.create(name, system_name, description, endpoint)
        backend = threescale.backends.read_by_name(system_name)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(backend.delete)
        return backend

    return _custom_ui_backend


@pytest.fixture(scope="module")
def ui_backend(custom_ui_backend, request):
    """Preconfigured backend existing over whole testing session"""
    name = blame(request, "ui_backend")
    return custom_ui_backend(name, name)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def custom_ui_product(custom_admin_login, navigator, threescale, testconfig, request):
    """Parametrized custom Product created via UI"""
    def _custom_ui_product(name: str, system_name: str, description: str = "", autoclean=True):
        custom_admin_login()
        product = navigator.navigate(ProductNewView)
        product.create(name, system_name, description)
        product = threescale.services.read_by_name(system_name)
        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(product.delete)
        return product

    return _custom_ui_product


@pytest.fixture(scope="module")
def ui_product(custom_ui_product, request):
    """Preconfigured product existing over whole testing session"""
    name = blame(request, "ui_product")
    return custom_ui_product(name, name)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def custom_ui_account(custom_admin_login, navigator, threescale, request, testconfig):
    """
    Create a custom account
    """
    def _custom_account(name: str, email: str, password: str, org_name: str, autoclean=True):
        custom_admin_login()
        account = navigator.navigate(AccountNewView)
        account.create(name, email, password, org_name)
        account = threescale.accounts.read_by_name(org_name)

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(account.delete)
        return account

    return _custom_account


@pytest.fixture(scope="module")
def ui_account(custom_ui_account, request):
    """Create an account through UI"""
    name = blame(request, "ui_account")
    return custom_ui_account(name, f"{name}@anything.invalid", name, name)


# custom_app_plan dependency is needed to ensure cleanup in correct order
@pytest.fixture(scope="module")
def custom_ui_application(custom_app_plan, custom_admin_login, navigator, request, testconfig):
    """
    :return: params for custom application
    """
    def _custom_ui_application(name: str, description: str, plan: ApplicationPlan, account: Account, autoclean=True):
        custom_admin_login()
        app = navigator.navigate(ApplicationNewView, account=account)
        app.create(name, description, plan)
        application = account.applications.read_by_name(name)

        application.api_client_verify = testconfig["ssl_verify"]

        if autoclean and not testconfig["skip_cleanup"]:
            def delete():
                application.delete()

            request.addfinalizer(delete)
        return application

    return _custom_ui_application


@pytest.fixture(scope="module")
def ui_application(service, custom_app_plan, custom_ui_application, account, request):
    """Create an application through UI"""
    name = blame(request, "ui_account")
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_ui_application(name, "description", plan, account)


def pytest_exception_interact(node, call, report):
    """
        Method that is being invoked, when a test fails (hook)

        From py-test documentation:
            "Called when an exception was raised which can potentially be interactively handled."

        For more information about this method, please see:
            https://docs.pytest.org/en/stable/_modules/_pytest/hookspec.html#pytest_exception_interact

       :param node: info about the called test. What test was called, when it was called, which session etc.
       :param call: in depth summary of what exception was thrown
       :param report: generated summary of the test output
    """
    if report.failed:
        browser = node.funcargs.get("browser")
        screenshot = os.path.join(get_resultsdir_path(node), "failed-test-screenshot.png")
        browser.selenium.save_screenshot(screenshot)


def get_resultsdir_path(node):
    """
        Method that gives you the path where you should store screenshots. It also creates the dirs on the road.
    """

    xml = node.config.getoption('--junitxml')
    # path to "3scape-py-testsuite" folder
    no_argument_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..')
    resultsdir = os.environ.get("resultsdir", no_argument_dir)
    failed_test_name = node.nodeid.replace('/', '.').replace('.py::', '.')

    if not xml:
        path = f"{resultsdir}/attachments/ui/{failed_test_name}/"

    else:
        directory = os.path.dirname(xml)

        if directory == "":
            directory = "."

        # gets the file with extension and then it splits on the "." and returns only the name
        name = os.path.splitext(os.path.basename(xml))[0]
        path = f"{directory}/attachments/{name}/{failed_test_name}/"

    if not os.path.exists(path):
        os.makedirs(path)

    return path
