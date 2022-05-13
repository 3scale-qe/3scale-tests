"""Test for login into devel portal via recaptch on"""
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from testsuite import settings, rawobj
from testsuite.ui.views.admin.audience.developer_portal import SpamProtection
from testsuite.ui.views.devel.login import DeveloperSignUpView, LoginDevelView, SuccessfulAccountCreation, \
    DevelForgotPassword
from testsuite.utils import blame


@pytest.fixture(scope="function")
def ui_devel_account(request, testconfig, threescale):
    """
    Creates a unique username and deletes account associated with it after the test finishes running
    """
    user_name = blame(request, "username")

    yield user_name

    if not testconfig["skip_cleanup"]:
        usr = threescale.accounts.read_by_name(user_name)

        def finalizer():
            usr.delete()

        request.addfinalizer(finalizer)


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def devel_open_portal(browser, navigator, provider_account):
    """
    Opens the developer portal and passes in the access code.
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    """
    url = settings["threescale"]["devel"]["url"]
    browser.url = url
    browser.selenium.delete_all_cookies()
    page = navigator.open(LoginDevelView, access_code=provider_account['site_access_code'])
    page.wait_displayed()


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def spam_protection_setup(custom_admin_login, browser, navigator):
    """
    Opens the developer portal and passes in the access code.
    :param browser: Browser instance
    :param navigator: Navigator Instance
    :param provider_account: Currently used provider account (tenant)
    """
    custom_admin_login()
    page = navigator.open(SpamProtection)
    page.wait_displayed()
    page.enable_always_protection()

    yield

    url = settings["threescale"]["admin"]["url"]
    browser.url = url
    page = navigator.open(SpamProtection)
    page.wait_displayed()
    page.disable_protection()


# pylint: disable=unused-argument
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6695")
def test_devel_recaptcha_sing_up(spam_protection_setup, devel_open_portal, ui_devel_account, navigator, browser):
    """
    Test
        - Navigates and fills up the Sign Up page on developer portal
        - Checks, whether the form can be submitted without the recaptcha checkbox checked
        - Checks the checkbox
        - Submits the form and checks that the success website appears
    """
    signup_view = navigator.open(DeveloperSignUpView)
    signup_view.wait_displayed()

    username = ui_devel_account
    email = f"{username}@anything.invalid"
    signup_view.sign_up(username, username, email, username, submit=False)

    assert not signup_view.signup_button.is_enabled

    signup_view.check_recaptcha()
    WebDriverWait(browser.selenium, 10)\
        .until(EC.element_to_be_clickable((By.XPATH, signup_view.signup_button.locator)))

    assert signup_view.signup_button.is_enabled

    signup_view.signup_button.click()

    login_success = SuccessfulAccountCreation(navigator.browser)
    assert login_success.is_displayed


# pylint: disable=unused-argument
def test_devel_forgot_password_recaptcha(spam_protection_setup, devel_open_portal, custom_account, navigator, request):
    """
    Test
        - Navigates and fills up the Sign Up page on developer portal
        - Checks, whether the form can be submitted without the recaptcha checkbox checked
        - Checks the checkbox
        - Submits the form and checks that the success website appears
    """
    name = blame(request, "ui_account")
    params = rawobj.Account(name, False, False)
    params.update(dict(name=name, username=name, email=f"{name}@anything.invalid"))
    _ = custom_account(params=params)

    forgot_pass = navigator.open(DevelForgotPassword)
    forgot_pass.wait_displayed()

    assert not forgot_pass.flash_message.is_displayed

    forgot_pass.reset_button.click()

    assert forgot_pass.flash_message.is_displayed
    assert forgot_pass.flash_message.string_in_flash_message("spam protection failed")

    forgot_pass.check_recaptcha()
    forgot_pass.fill_form(f"{name}@anything.invalid")
    forgot_pass.reset_button.click()

    login_view = LoginDevelView(navigator.browser)
    login_view.wait_displayed()

    assert login_view.flash_message.is_displayed
    assert login_view.flash_message.string_in_flash_message("password reset link")
