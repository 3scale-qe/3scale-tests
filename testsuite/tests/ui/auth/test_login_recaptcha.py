"""Test for login into admin portal with bot protection (recaptcha) enabled"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, settings
from testsuite.ui.views.admin.login import LoginView, RequestAdminPasswordView
from testsuite.ui.views.admin.settings.bot_protection import AdminBotProtection

pytestmark = [
    pytest.mark.usefixtures("login"),
    pytest.mark.usefixtures("bot_protection_setup"),
    pytest.mark.issue("https://redhat.atlassian.net/browse/THREESCALE-765"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.16"), reason="TESTED_VERSION < Version('2.16')"),
]


@pytest.fixture(scope="module")
def bot_protection_setup(navigator, browser):
    """
    Enables admin portal bot protection via UI,
    then clears session so subsequent tests see the unauthenticated login page.
    Requires recaptcha keys to be configured in 3scale settings.
    Session cookies are saved before deletion and restored in teardown to avoid
    circular dependency (recaptcha blocks selenium login during teardown).
    """
    bot_page = navigator.navigate(AdminBotProtection)
    bot_page.enable_protection()
    saved_cookies = browser.selenium.get_cookies()
    browser.selenium.delete_all_cookies()

    yield

    browser.selenium.get(settings["threescale"]["admin"]["url"])
    for cookie in saved_cookies:
        browser.selenium.add_cookie(cookie)
    browser.selenium.refresh()
    navigator.navigate(AdminBotProtection).disable_protection()


def test_admin_login_blocked_by_recaptcha(navigator):
    """
    Test
        - Navigates to the admin portal login page
        - Waits for reCAPTCHA to load and generate a token
        - Attempts to log in with valid credentials
        - Asserts that login is rejected due to low reCAPTCHA score from automated browser
    """
    login_page = navigator.open(LoginView, url=settings["threescale"]["admin"]["url"], wait_displayed=False)
    assert login_page.recaptcha.is_displayed, "Recaptcha was not found on the admin portal login page"
    login_page.browser.execute_script(  # hack to force reCAPTCHA V3 get bad score
        "window.grecaptcha.execute = () => Promise.resolve('');"
    )
    login_page.login_widget.do_login(
        settings["threescale"]["admin"]["username"], settings["threescale"]["admin"]["password"]
    )
    assert login_page.error_message.is_displayed, "Expected reCAPTCHA error message to be displayed"


@pytest.mark.xfail  # not implemented yet
def test_admin_forgot_password_blocked_by_recaptcha(navigator):
    """
    Test
        - Navigates to the admin portal forgot password page
        - Overrides reCAPTCHA token to force rejection
        - Submits a password reset request
        - Asserts that the request is rejected due to invalid reCAPTCHA token
    """
    forgot_pass = navigator.open(RequestAdminPasswordView, url=settings["threescale"]["admin"]["url"])
    assert forgot_pass.recaptcha.is_displayed, "Recaptcha was not found on the admin portal forgot password page"
    forgot_pass.browser.execute_script(  # hack to force reCAPTCHA V3 get bad score
        "window.grecaptcha.execute = () => Promise.resolve('');"
    )
    forgot_pass.reset_password(settings["threescale"]["admin"]["username"])
    assert forgot_pass.error_message.is_displayed, "Expected reCAPTCHA error message to be displayed"
