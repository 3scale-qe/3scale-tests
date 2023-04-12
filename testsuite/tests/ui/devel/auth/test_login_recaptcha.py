"""Test for login into devel portal with spam protection enabled"""
import pytest

from testsuite import settings, rawobj
from testsuite.ui.views.admin.audience.developer_portal import SpamProtection
from testsuite.ui.views.devel.login import BasicSignUpView, LoginView, SuccessfulAccountCreationView, \
    ForgotPasswordView
from testsuite.utils import blame

# requires special setup, internet access
pytestmark = pytest.mark.sandbag


@pytest.fixture(scope="function")
def ui_devel_account(request, threescale):
    """
    Creates a unique username and deletes account associated with it after the test finishes running
    """
    user_name = blame(request, "username")

    yield user_name

    usr = threescale.accounts.read_by_name(user_name)
    request.addfinalizer(usr.delete)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def spam_protection_setup(login, navigator):
    """
    Opens the developer portal and passes in the access code.
    """
    spam_page = navigator.open(SpamProtection)
    assert spam_page.sus_protection.is_enabled, "Missing recaptcha setup in 3scale"
    assert spam_page.always_protection.is_enabled, "Missing recaptcha setup in 3scale"
    spam_page.enable_always_protection()

    yield

    page = navigator.open(SpamProtection, url=settings["threescale"]["admin"]["url"])
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
def test_devel_recaptcha_sing_up(spam_protection_setup, provider_account, ui_devel_account, navigator):
    """
    Test
        - Navigates and fills up the Sign Up page on developer portal
        - Checks, whether the form can be submitted without the recaptcha checkbox checked
        - Checks the checkbox
        - Submits the form and checks that the success website appears
    """
    signup_view = navigator.open(BasicSignUpView, url=settings["threescale"]["devel"]["url"],
                                 access_code=provider_account['site_access_code'])

    username = ui_devel_account
    email = f"{username}@anything.invalid"
    signup_view.sign_up(username, username, email, username, submit=False)

    assert not signup_view.signup_button.is_enabled
    assert signup_view.recaptcha.is_displayed, "Recaptcha was not found on the developer sign up page"
    signup_view.check_recaptcha()
    assert signup_view.signup_button.is_enabled

    signup_view.signup_button.click()

    login_success = SuccessfulAccountCreationView(navigator.browser)
    assert login_success.is_displayed


def test_devel_forgot_password_recaptcha(spam_protection_setup, custom_account, navigator, params):
    """
    Test
        - Navigates and fills up the Lost password page on developer portal
        - Checks, whether the form can be submitted without the recaptcha checkbox checked
        - Checks the checkbox
        - Submits the form and checks that the success website appears
    """
    custom_account(params=params)
    forgot_pass = navigator.open(ForgotPasswordView)

    assert not forgot_pass.flash_message.is_displayed
    assert forgot_pass.recaptcha.is_displayed, "Recaptcha was not found on the developer sign up page"
    forgot_pass.reset_button.click()

    assert forgot_pass.flash_message.is_displayed
    assert forgot_pass.flash_message.string_in_flash_message("spam protection failed")

    forgot_pass.check_recaptcha()
    forgot_pass.fill_form(f"{params['email']}")
    forgot_pass.reset_button.click()

    login_view = LoginView(navigator.browser)

    assert login_view.flash_message.is_displayed
    assert login_view.flash_message.string_in_flash_message("a password reset link has been emailed to you")
