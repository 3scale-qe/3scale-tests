"""UI Login smoketests"""

import pytest

from testsuite.config import settings
from testsuite.ui.views.admin.login import LoginView


@pytest.fixture(scope="module")
def browser(browser):
    """Displays Admin pages when browser is created"""
    browser.url = settings["threescale"]["admin"]["url"]
    return browser


@pytest.fixture(scope="function")
def refreshed_browser(browser):
    """
    This fixture will reload login page to overcome problem of reseting text
    input
    """
    browser.selenium.delete_all_cookies()
    browser.selenium.refresh()
    return browser


@pytest.mark.smoke
def test_login_page_text(refreshed_browser):
    """
    Test expected strings on the Login page
    """
    assert LoginView(refreshed_browser).is_displayed


@pytest.mark.smoke
def test_log_with_empty_password(refreshed_browser):
    """
    Test Login button is disabled if only name is filled
    """
    login_view = LoginView(refreshed_browser)
    login_view.login_widget.username_field.fill("username")
    assert not login_view.login_widget.submit.is_enabled


@pytest.mark.smoke
def test_log_with_empty_username(refreshed_browser):
    """
    Test Login button is disabled if only password is filled
    """
    login_view = LoginView(refreshed_browser)
    login_view.login_widget.password_field.fill("password")
    assert not login_view.login_widget.submit.is_enabled


@pytest.mark.smoke
def test_log_with_random_username_password(refreshed_browser):
    """
    Test Login button is enabled after filling form and expect incorrect credentials
    """
    login_view = LoginView(refreshed_browser)
    login_view.login_widget.username_field.fill("username")
    login_view.login_widget.password_field.fill("password")
    assert login_view.login_widget.submit.is_enabled
    login_view.login_widget.submit.click()
    assert "Incorrect email or password. Please try again" in login_view.error_message.text
