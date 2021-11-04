"UI conftest"

import os

import backoff
import pytest
from auth0.v3.management import auth0
from threescale_api.resources import Account, ApplicationPlan, Service

from testsuite import rawobj
from testsuite.auth0 import auth0_token
from testsuite.billing import Stripe, Braintree
from testsuite.config import settings
from testsuite.tests.ui import Sessions
from testsuite.ui.browser import ThreeScaleBrowser
from testsuite.ui.navigation import Navigator
from testsuite.ui.views.admin.audience.account import AccountNewView
from testsuite.ui.views.admin.audience.application import ApplicationNewView
from testsuite.ui.views.admin.backend.backend import BackendNewView
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.login import LoginView
from testsuite.ui.views.admin.product.application import ApplicationPlanNewView
from testsuite.ui.views.admin.product.product import ProductNewView
from testsuite.ui.views.devel.login import LoginDevelView
from testsuite.ui.views.master.audience.tenant import TenantNewView
from testsuite.ui.views.master.foundation import BaseMasterView
from testsuite.ui.views.master.login import MasterLoginView
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
        name = name or settings["threescale"]["admin"]["username"]
        password = password or settings["threescale"]["admin"]["password"]
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


@pytest.fixture
def master_login(browser, navigator):
    """
    Login to the Master portal with default admin credentials
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :return: Login with default credentials
    """
    url = settings["threescale"]["master"]["url"]
    name = settings["threescale"]["master"]["username"]
    password = settings["threescale"]["master"]["password"]
    browser.url = url

    page = navigator.open(MasterLoginView)

    if page.is_displayed:
        page.do_login(name, password)


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
            cookies = [cookie for cookie in cookies if cookie is not None]
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
        BaseAdminView,
        BaseMasterView
    ]
    navigator = Navigator(browser, base_views)
    return navigator


# pylint: disable=unused-argument, too-many-arguments
@pytest.fixture(scope="module")
def custom_ui_tenant(navigator, threescale, testconfig, request, master_threescale):
    """Parametrized custom Tenant created via UI"""

    def _custom_ui_tenant(username: str = "",
                          email: str = "",
                          password: str = "",
                          organisation: str = "",
                          autoclean=True):

        tenant = navigator.navigate(TenantNewView)

        tenant.create(username=username, email=email+"@anything.invalid", password=password, organization=organisation)

        account = master_threescale.accounts.read_by_name(organisation)
        tenant = master_threescale.tenants.read(account.entity_id)
        tenant.wait_tenant_ready()

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(tenant.delete)

        return tenant

    return _custom_ui_tenant


@pytest.fixture(scope="module")
def ui_tenant(custom_ui_tenant, request):
    """Preconfigured tenant existing over whole testing session"""
    name = blame(request, "ui-tenant")
    return custom_ui_tenant(username=name, email=name, password="12345678", organisation=name)


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

    def _custom_ui_application(name: str, description: str, plan: ApplicationPlan, account: Account, service: Service,
                               autoclean=True):
        custom_admin_login()
        app = navigator.navigate(ApplicationNewView, account=account)
        app.create(name, description, plan, service)
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
    return custom_ui_application(name, "description", plan, account, service)


@pytest.fixture(scope="module")
def custom_ui_app_plan(custom_admin_login, navigator):
    """Create custom application plan via UI"""

    def _custom_ui_app_plan(name: str, service: Service):
        custom_admin_login()
        plan = navigator.navigate(ApplicationPlanNewView, product=service)
        plan.create(name, name)
        app_plan = service.app_plans.read_by_name(name)

        return app_plan

    return _custom_ui_app_plan


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
        if not browser:
            return
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


@pytest.fixture(scope="module")
def custom_auth0_login(browser, navigator, threescale, request, testconfig):
    """
    Login fixture for admin portal via Auth0.
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param threescale: 3scale API client
    :param request: We need this to be able to delete automatic created user after tests.
    :return: Login to Admin portal with custom credentials
    """

    def _login(email=None, password=None, autoclean=True):
        browser.selenium.delete_all_cookies()
        browser.refresh()
        browser.url = settings["threescale"]["admin"]["url"]
        page = navigator.open(LoginView)
        page.do_auth0_login(email, password)

        def _delete():
            name = email.split("@")[0]
            user = threescale.provider_account_users.read_by_name(name)
            user.delete()

        if not testconfig["skip_cleanup"] and autoclean:
            request.addfinalizer(_delete)

    return _login


@pytest.fixture(scope="module")
def custom_rhsso_login(browser, navigator, threescale, request, testconfig, rhsso_service_info):
    """
    Login fixture for admin portal via RHSSO.
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param threescale: 3scale API client
    :param request: We need this to be able to delete automatic created user after tests.
    :return: Login to Admin portal with custom credentials
    """

    def _login(username, password, rhsso_username=None):
        browser.selenium.delete_all_cookies()
        browser.refresh()
        user_id = rhsso_service_info.realm.admin.get_user_id(username)
        rhsso_service_info.realm.admin.logout(user_id)
        browser.url = settings["threescale"]["admin"]["url"]
        page = navigator.open(LoginView)
        page.do_rhsso_login(username, password)

        def _delete():
            user = threescale.provider_account_users.read_by_name(rhsso_username)
            user.delete()

        if not testconfig["skip_cleanup"] and rhsso_username:
            request.addfinalizer(_delete)

    return _login


@pytest.fixture(scope="module")
def auth0_client(testconfig):
    """
    API client for Auth0
    """
    return auth0.Auth0(testconfig["auth0"]["domain"], auth0_token())


@pytest.fixture(scope="module")
def set_callback_urls(auth0_client):
    """
    Set callback urls for Auth0 application
    """
    cleanup = []

    @backoff.on_predicate(backoff.fibo, lambda x: not x['callbacks'], 8, jitter=None)
    def _get_auth_client(client_id):
        return auth0_client.clients.get(client_id)

    def _set_callback_urls(client_id, urls: list):
        auth0_client.clients.update(client_id, body={"callbacks": urls})
        cleanup.append(client_id)
        return _get_auth_client(client_id)

    yield _set_callback_urls
    for client in cleanup:
        auth0_client.clients.update(client, body={"callbacks": []})


@pytest.fixture(scope="module")
def auth0_user_password():
    """Password for auth0 user"""
    return "RedHat123"


@pytest.fixture(scope="module")
def auth0_user(auth0_client, request, testconfig, auth0_user_password):
    """
    Create Auth0 user via Auth0 API
    """
    name = blame(request, "auth_user")
    user = auth0_client.users.create({"email": f"{name}@anything.invalid", "password": auth0_user_password,
                                      "connection": "Username-Password-Authentication", "email_verified": True})
    if not testconfig["skip_cleanup"]:
        def _delete():
            auth0_client.users.delete(user["user_id"])

        request.addfinalizer(_delete)
    return user


@pytest.fixture(scope='session')
def stripe():
    """Stripe API"""
    return Stripe(settings["stripe"]["api_key"])


@pytest.fixture(scope='session')
def braintree():
    """Braintree API"""
    braintree_credentials = settings["braintree"]
    merchant_id = braintree_credentials['merchant_id']
    public_key = braintree_credentials['public_key']
    private_key = braintree_credentials['private_key']
    return Braintree(merchant_id, public_key, private_key)
