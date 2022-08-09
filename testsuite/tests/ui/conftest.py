"UI conftest"

import io
import math
import os
import traceback
from datetime import datetime

import backoff
import pytest
import pytest_html
from PIL import Image
from auth0.v3.management import auth0
from threescale_api.resources import Account, ApplicationPlan, Service

from testsuite import rawobj, resilient
from testsuite.auth0 import auth0_token
from testsuite.billing import Stripe, Braintree
from testsuite.config import settings
from testsuite.tests.ui import Sessions
from testsuite.ui.browser import ThreeScaleBrowser
from testsuite.ui.navigation import Navigator
from testsuite.ui.views.admin.audience.account import AccountNewView
from testsuite.ui.views.admin.audience.application import ApplicationNewView
from testsuite.ui.views.admin.backend.backend import BackendNewView
from testsuite.ui.views.admin.login import LoginView
from testsuite.ui.views.admin.product.application import ApplicationPlanNewView
from testsuite.ui.views.admin.product.product import ProductNewView
from testsuite.ui.views.devel.login import LoginDevelView
from testsuite.ui.views.master.audience.tenant import TenantNewView
from testsuite.ui.views.master.login import MasterLoginView
from testsuite.ui.webdriver import SeleniumDriver
from testsuite.utils import blame


@pytest.fixture(scope="session")
def webdriver():
    """Creates instance of Web Driver with configuration"""
    return SeleniumDriver(source=settings["fixtures"]["ui"]["browser"]["source"],
                          driver=settings["fixtures"]["ui"]["browser"]["webdriver"],
                          ssl_verify=settings["ssl_verify"],
                          remote_url=settings["fixtures"]["ui"]["browser"]["remote_url"],
                          binary_path=settings["fixtures"]["ui"]["browser"]["binary_path"])


@pytest.fixture(scope="session")
def browser(webdriver, request):
    """
    Browser representation based on UI settings
    Args:
        :param webdriver: Selenium driver configuration
        :param request: Finalizer for session cleanup
        :return browser: Browser instance
    """
    webdriver.get_driver()
    webdriver.post_init()
    started_browser = ThreeScaleBrowser(selenium=webdriver.webdriver)
    request.addfinalizer(webdriver.finalize)
    return started_browser


@pytest.fixture(scope="session")
def sessions():
    """Sessions that were stored during test run"""
    return Sessions()


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

        if not sessions.restore(browser, name, password, url):
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

        if not sessions.restore(browser, name, password, url):
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
    navigator = Navigator(browser)
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

        account = resilient.resource_read_by_name(master_threescale.accounts, organisation)
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
        backend = resilient.resource_read_by_name(threescale.backends, system_name)
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
        product = resilient.resource_read_by_name(threescale.services, system_name)
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
        account = resilient.resource_read_by_name(threescale.accounts, org_name)

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
        application = resilient.resource_read_by_name(account.applications, name)

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
        app_plan = resilient.resource_read_by_name(service.app_plans, name)

        return app_plan

    return _custom_ui_app_plan


def pytest_html_results_table_html(report, data):
    """
    Make image path relative to resultsdir; skip logs if passed

    For obvious reason this is heavily dependent on html report structure,
    if that change this will stop working
    """
    if report.passed:
        del data[:]

    resultsdir = "%s/" % _resultsdir().rstrip("/")
    for i in data:
        try:
            href = i[0].attr.href
            img = i[0][0].uniobj
        except (TypeError, AttributeError, IndexError):
            continue
        if href:
            i[0].attr.href = i[0].attr.href.replace(resultsdir, "", 1)
        if img:
            i[0][0].uniobj = i[0][0].uniobj.replace(resultsdir, "", 1)


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

        try:
            filepath = fullpage_screenshot(driver=browser.selenium, file_path=get_resultsdir_path(node))
            extra = getattr(report, "extra", [])
            extra.append(pytest_html.extras.image(filepath))
        # pylint: disable=broad-except
        except Exception:
            traceback.print_exc()


def _resultsdir():
    """Return path to resultsdir"""
    no_argument_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..')
    return os.environ.get("resultsdir", no_argument_dir)


def get_resultsdir_path(node):
    """
        Method that gives you the path where you should store screenshots. It also creates the dirs on the road.
    """

    xml = node.config.getoption('--junitxml')
    resultsdir = _resultsdir()
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


def fullpage_screenshot(driver, file_path):
    """
        A full-page screenshot function. It scroll the website and screenshots it.
        - Creates multiple files
        - Screenshots are made only vertically (on Y axis)
    """
    # Removal of the height: 100% style, that disables scroll.
    driver.execute_script("document.body.style.height = 'unset'")
    driver.execute_script("document.body.parentNode.style.height = 'unset'")

    total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")

    screenshot_bytes = driver.get_screenshot_as_png()
    screenshot = Image.open(io.BytesIO(screenshot_bytes))
    width, height = screenshot.size
    del screenshot

    scaling_constant = (float(height) / float(viewport_height))
    stitched_image = Image.new('RGB', (width, int(total_height * scaling_constant)))
    part = 0

    for scroll in range(0, total_height, viewport_height):
        driver.execute_script("window.scrollTo({0}, {1})".format(0, scroll))
        screenshot_bytes = driver.get_screenshot_as_png()
        screenshot = Image.open(io.BytesIO(screenshot_bytes))

        if scroll + viewport_height > total_height:
            offset = (0, int(math.ceil((total_height - viewport_height) * scaling_constant)))
        else:
            offset = (0, int(math.ceil(scroll * scaling_constant)))

        stitched_image.paste(screenshot, offset)
        del screenshot
        part += 1

    date = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
    fullpath = f"{file_path}/{date}.png"
    stitched_image.save(fullpath)
    return fullpath


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
            user = resilient.resource_read_by_name(threescale.provider_account_users, name)
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
        rhsso_service_info.realm.admin.user_logout(user_id)
        browser.url = settings["threescale"]["admin"]["url"]
        page = navigator.open(LoginView)
        page.do_rhsso_login(username, password)

        def _delete():
            user = resilient.resource_read_by_name(threescale.provider_account_users, rhsso_username)
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

    @backoff.on_predicate(backoff.fibo, lambda x: not x['callbacks'], max_tries=8, jitter=None)
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
