"""Test for login into devel portal with spam protection enabled"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import settings, rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.ui.views.admin.audience.developer_portal import BotProtection
from testsuite.ui.views.devel.login import BasicSignUpView, LoginView, SuccessfulAccountCreationView, ForgotPasswordView
from testsuite.utils import blame, warn_and_skip

# requires special setup, internet access
pytestmark = [pytest.mark.sandbag, pytest.mark.usefixtures("login"), pytest.mark.usefixtures("spam_protection_setup")]


@pytest.fixture(scope="module")
def skip_rhoam(testconfig):
    """Recaptcha requires special setup unavailable on RHOAM"""
    if testconfig["threescale"]["deployment_type"] == "rhoam":
        warn_and_skip(skip_rhoam.__doc__)


@pytest.fixture(scope="function")
def ui_devel_account(request, testconfig, threescale):
    """
    Creates a unique username and deletes account associated with it after the test finishes running
    """
    user_name = blame(request, "username")

    yield user_name

    if not testconfig["skip_cleanup"]:
        usr = threescale.accounts.read_by_name(user_name)
        request.addfinalizer(usr.delete)


@pytest.fixture(scope="module")
def spam_protection_setup(navigator):
    """
    Opens the developer portal and passes in the access code.
    """
    spam_page = navigator.open(BotProtection)
    assert spam_page.recaptcha_protection.is_enabled, "Missing recaptcha setup in 3scale"
    spam_page.enable_protection()

    yield

    page = navigator.open(BotProtection, url=settings["threescale"]["admin"]["url"])
    page.disable_protection()


@pytest.fixture(scope="function")
def params(request):
    """
    @return: params for custom account
    """
    name = blame(request, "ui_account")
    params = rawobj.Account(name, monthly_billing_enabled=False, monthly_charging_enabled=False)
    params.update({"name": name, "username": name, "email": f"{name}@anything.invalid"})
    return params


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6695")
def test_devel_recaptcha_sing_up(provider_account, ui_devel_account, navigator):
    """
    Test
        - Navigates and fills up the Sign Up page on developer portal
        - Assert that invisible recaptcha badge is present
        - Submits the form and checks that the success website appears
    """
    signup_view = navigator.open(
        BasicSignUpView, url=settings["threescale"]["devel"]["url"], access_code=provider_account["site_access_code"]
    )

    username = ui_devel_account
    email = f"{username}@anything.invalid"
    signup_view.sign_up(username, username, email, username, submit=False)

    assert signup_view.signup_button.is_enabled
    assert signup_view.recaptcha.is_displayed, "Recaptcha was not found on the developer sign up page"

    signup_view.signup_button.click()

    login_success = SuccessfulAccountCreationView(navigator.browser)
    assert login_success.is_displayed


def test_devel_forgot_password_recaptcha(custom_account, navigator, params):
    """
    Test
        - Navigates and fills up the Lost password page on developer portal
        - Assert that invisible recaptcha badge is present
        - Submits the form and assert that the success website appears
    """
    custom_account(params=params)
    forgot_pass = navigator.open(ForgotPasswordView)

    assert not forgot_pass.flash_message.is_displayed
    assert forgot_pass.recaptcha.is_displayed, "Recaptcha was not found on the developer forgot password page"


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10579")
@pytest.mark.skipif("TESTED_VERSION < Version('2.15')")
def test_devel_login_recaptcha(custom_account, navigator, params):
    """
    Test
        - Navigates to the developer portal login view
        - Assert that invisible recaptcha badge is present
    """
    custom_account(params=params)
    login_view = navigator.open(LoginView)

    assert login_view.recaptcha.is_displayed, "Recaptcha was not found on the developer login page"
