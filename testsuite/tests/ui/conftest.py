"UI conftest"
# pylint: disable=too-many-arguments, unused-argument

import io
import logging
import math
import os
from datetime import datetime

import backoff
import pytest
import pytest_html
from auth0.management import auth0
from selenium.common import InvalidSessionIdException, WebDriverException
from threescale_api.resources import Account, ApplicationPlan, Service
from PIL import Image

from testsuite import rawobj, resilient
from testsuite.auth0 import auth0_token
from testsuite.config import settings
from testsuite.ui.browser import ThreeScaleBrowser
from testsuite.ui.navigation import Navigator
from testsuite.ui.views.admin.foundation import DashboardView
from testsuite.ui.views.admin.audience.account import AccountNewView, AccountsView
from testsuite.ui.views.admin.audience.application import ApplicationNewView, ApplicationsView
from testsuite.ui.views.admin.product.product import ProductsView
from testsuite.ui.views.admin.backend.backend import BackendNewView
from testsuite.ui.views.admin.login import LoginView
from testsuite.ui.views.admin.product.application import ApplicationPlanNewView
from testsuite.ui.views.admin.product.product import ProductNewView
from testsuite.ui.views.devel.login import LoginView as DeveloperLoginView
from testsuite.ui.views.master.audience.tenant import TenantNewView, TenantDetailView
from testsuite.ui.views.master.login import MasterLoginView
from testsuite.ui.webdriver import ThreescaleWebdriver
from testsuite.utils import blame


LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def webdriver():
    """Creates instance of Web Driver with configuration"""
    return ThreescaleWebdriver(
        source=settings["fixtures"]["ui"]["browser"]["source"],
        driver=settings["fixtures"]["ui"]["browser"]["webdriver"],
        ssl_verify=settings["ssl_verify"],
        headless=settings["fixtures"]["ui"]["browser"]["headless"],
        remote_url=settings["fixtures"]["ui"]["browser"]["remote_url"],
        binary_path=settings["fixtures"]["ui"]["browser"]["binary_path"],
    )


@pytest.fixture(scope="module")
def browser(webdriver, request, metadata):
    """
    Browser representation based on UI settings
    Args:
        :param webdriver: Selenium driver configuration
        :param request: Finalizer for session cleanup
        :param metadata: Test session metadata
        :return browser: Browser instance
    """
    browser = ThreeScaleBrowser(webdriver=webdriver)
    request.addfinalizer(webdriver.finalize)
    caps = webdriver.webdriver.webdriver.caps
    metadata["Browser"] = f"{caps['browserName']} {caps['browserVersion']}"
    return browser


@pytest.fixture(scope="module")
def navigator(browser):
    """
    Navigator for 3scale UI pages/Views
    :param browser: browser based on UI settings
    :return: Navigator instance
    """
    navigator = Navigator(browser)
    return navigator


@pytest.fixture(scope="module")
def custom_admin_login(navigator, browser):
    """
    Returns parametrized Login fixture for Admin portal.
    To remove cookies and previous login session (from Admin portal), set `fresh` flag to True.
    :param navigator: Navigator Instance
    :param browser: Browser instance
    :return: Login to Admin portal with custom credentials
    """

    @backoff.on_exception(
        backoff.constant,
        InvalidSessionIdException,
        max_tries=2,
        jitter=None,
        on_backoff=lambda _: browser.restart_session(),
    )
    def _login(name=None, password=None, fresh=None):
        url = settings["threescale"]["admin"]["url"]
        name = name or settings["threescale"]["admin"]["username"]
        password = password or settings["threescale"]["admin"]["password"]
        page = navigator.open(LoginView, url=url, wait_displayed=False)

        if fresh:
            browser.selenium.delete_all_cookies()
            browser.selenium.refresh()
        if page.is_displayed:
            page.do_login(name, password)

    return _login


@pytest.fixture(scope="module")
def login(custom_admin_login):
    """
    Login to the Admin portal with default admin credentials
    :param custom_admin_login: Parametrized login method
    :return: Login with default credentials
    """
    return custom_admin_login()


@pytest.fixture(scope="module")
def master_login(navigator):
    """
    Login to the Master portal with default admin credentials
    :param navigator: Navigator Instance
    :return: Login with default credentials
    """
    url = settings["threescale"]["master"]["url"]
    name = settings["threescale"]["master"]["username"]
    password = settings["threescale"]["master"]["password"]
    page = navigator.open(MasterLoginView, url=url)

    if page.is_displayed:
        page.do_login(name, password)


@pytest.fixture(scope="module")
def custom_devel_login(navigator, provider_account, account_password, browser):
    """
    Login to Developer portal with specific account or credentials
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    :param account_password: fixture that returns default account password
    :return: Login to Developer portal with custom credentials (account or name-password pair)
    """

    def _login(account=None, name=None, password=None, fresh=None):
        url = settings["threescale"]["devel"]["url"]
        name = name or account["org_name"]
        password = password or account_password
        if fresh:
            browser.selenium.delete_all_cookies()
            browser.selenium.refresh()
        page = navigator.open(
            DeveloperLoginView, url=url, wait_displayed=False, access_code=provider_account["site_access_code"]
        )
        if page.is_displayed:
            page.do_login(name, password)

    return _login


@pytest.fixture(scope="module")
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
def custom_ui_tenant(master_login, navigator, threescale, testconfig, request, master_threescale, browser):
    """Parametrized custom Tenant created via UI"""

    @backoff.on_predicate(
        backoff.constant,
        lambda ready: not ready,
        interval=6,
        max_tries=5,
        jitter=None,
        on_backoff=lambda _: browser.selenium.refresh(),
    )
    def _wait_displayed_with_refresh(func):
        """Runs function and expects True. If False is returned, backoff and browser refresh happens."""
        return func()

    def _ui_wait_tenant_ready(tenant):
        """
        When assert is not raised, there is some chance the tenant is actually ready.
        Ui version of tenant.wait_for_tenant
        """
        tenant = navigator.navigate(TenantDetailView, account=tenant)
        with browser.new_tab(tenant.impersonate):
            assert _wait_displayed_with_refresh(lambda: DashboardView(browser).is_displayed)
            assert _wait_displayed_with_refresh(
                lambda: navigator.navigate(AccountsView).table.row()[0].text != "No results."
            )
            assert _wait_displayed_with_refresh(
                lambda: navigator.navigate(ApplicationsView).table.row()[0].text != "No results."
            )
            assert _wait_displayed_with_refresh(
                lambda: navigator.navigate(ProductsView).table.row()[0].text != "No results."
            )

    def _custom_ui_tenant(
        username: str = "", email: str = "", password: str = "", organisation: str = "", autoclean=True, wait=True
    ):
        tenant = navigator.navigate(TenantNewView)

        tenant.create(
            username=username, email=email + "@anything.invalid", password=password, organization=organisation
        )

        account = resilient.resource_read_by_name(master_threescale.accounts, organisation)
        tenant = master_threescale.tenants.read(account.entity_id)

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(tenant.delete)

        if wait:
            _ui_wait_tenant_ready(tenant)

        return tenant

    return _custom_ui_tenant


@pytest.fixture(scope="module")
def ui_tenant(custom_ui_tenant, request):
    """Preconfigured tenant existing over whole testing session"""
    name = blame(request, "ui-tenant")
    return custom_ui_tenant(username=name, email=name, password="12345678", organisation=name)


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

    def _custom_ui_application(
        name: str, description: str, plan: ApplicationPlan, account: Account, service: Service, autoclean=True
    ):
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


# this is set in pytest_exception_interact() and used
# in pytest_html_results_table_html() as it is not directly accessible there
html_report = None  # pylint: disable=invalid-name


def pytest_html_results_table_html(report, data):
    """
    Make image path relative to resultsdir; skip logs if passed

    For obvious reason this is heavily dependent on html report structure,
    if that change this will stop working
    """
    if report.passed:
        del data[:]

    for i in data:
        href = None
        img = None
        try:
            basedir = os.path.dirname(html_report)
            href = i[0].attr.href
            img = i[0][0].uniobj
        except (TypeError, AttributeError, IndexError):
            continue
        if href:
            i[0].attr.href = os.path.relpath(href, start=basedir)
        if img:
            new = os.path.relpath(href, start=basedir)
            i[0][0].uniobj = i[0][0].uniobj.replace(href, new, 1)


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
    if report.failed or hasattr(report, "wasxfail"):
        browser = node.funcargs.get("browser")
        if not browser:
            LOGGER.info("Screenshot was not created. Browser was None. ")
            return

        dir_path = get_resultsdir_path(node)
        try:
            filepath = fullpage_screenshot(driver=browser.selenium, file_path=dir_path)
            extra = getattr(report, "extra", [])
            extra.append(pytest_html.extras.image(filepath))
            report.extra = extra
            LOGGER.info("Screenshot %s was created for the URL: %s", dir_path, browser.url)

            global html_report  # pylint: disable=global-statement
            html_report = node.config.getoption("--html")

        except (InvalidSessionIdException, WebDriverException):
            LOGGER.info(
                "Can't create a screenshot. Browser session %s is already closed.",
                browser.webdriver.session.session_id,
            )
            if len(os.listdir(dir_path)) == 0:
                os.removedirs(dir_path)


def get_resultsdir_path(node):
    """
    Method that gives you the path where you should store screenshots. It also creates the dirs on the road.
    """

    xml = node.config.getoption("--junitxml")
    # path to "3scape-py-testsuite" folder
    no_argument_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../..")
    resultsdir = os.environ.get("resultsdir", no_argument_dir)
    failed_test_name = node.nodeid.replace("/", ".").replace(".py::", ".")

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


# pylint: disable=too-many-locals
def fullpage_screenshot(driver, file_path):
    """
    A full-page screenshot function. It scrolls the website and screenshots it.
    - Creates multiple files
    - Screenshots are made only vertically (on Y axis)
    """
    try:
        # Removal of the height: 100% style, that disables scroll.
        driver.execute_script("document.body.style.height = 'unset'")
        driver.execute_script("document.body.parentNode.style.height = 'unset'")

        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")

        screenshot_bytes = driver.get_screenshot_as_png()
        screenshot = Image.open(io.BytesIO(screenshot_bytes))
        width, height = screenshot.size
        del screenshot

        scaling_constant = float(height) / float(viewport_height)
        stitched_image = Image.new("RGB", (width, int(total_height * scaling_constant)))
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

        date = datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        fullpath = f"{file_path}/{date}.png"
        stitched_image.save(fullpath)
        return fullpath
    # pylint: disable=broad-exception-caught
    except Exception as e:
        return f"Error: Failed to take full-page screenshot. Details: {str(e)}"


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
        page = navigator.open(LoginView, wait_displayed=False)
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
        page = navigator.open(LoginView, wait_displayed=False)
        page.do_rhsso_login(username, password, realm=rhsso_service_info.realm.name)

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

    @backoff.on_predicate(backoff.fibo, lambda x: not x["callbacks"], max_tries=8, jitter=None)
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
    user = auth0_client.users.create(
        {
            "email": f"{name}@anything.invalid",
            "password": auth0_user_password,
            "connection": "Username-Password-Authentication",
            "email_verified": True,
        }
    )
    if not testconfig["skip_cleanup"]:

        def _delete():
            auth0_client.users.delete(user["user_id"])

        request.addfinalizer(_delete)
    return user
