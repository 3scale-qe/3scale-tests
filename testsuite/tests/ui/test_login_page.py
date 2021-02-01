"""UI Login smoketests"""

import pytest
from testsuite.ui.views.admin import LoginView


@pytest.fixture(scope="function")
def refreshed_browser(browser):
    """
    This fixture will reload login page to overcome problem of reseting text
    input
    """
    url = browser.url
    browser.url = "data:,"
    browser.url = url  # reload to login page
    return browser


@pytest.mark.smoke
def test_login_page_text(browser):
    """
    Test expected strings on the Login page
    """
    assert LoginView(browser).has_content


@pytest.mark.smoke
def test_log_with_empty_password(refreshed_browser):
    """
    Test Login button is disabled if only name is filled
    """
    LoginView(refreshed_browser).username_field.fill("username")
    assert not LoginView(refreshed_browser).submit.is_enabled


@pytest.mark.smoke
def test_log_with_empty_username(refreshed_browser):
    """
    Test Login button is disabled if only password is filled
    """
    LoginView(refreshed_browser).password_field.fill("password")
    assert not LoginView(refreshed_browser).submit.is_enabled


@pytest.mark.smoke
def test_log_with_random_username_password(refreshed_browser):
    """
    Test Login button is enabled after filling form and expect incorrect credentials
    """
    LoginView(refreshed_browser).username_field.fill("username")
    LoginView(refreshed_browser).password_field.fill("password")
    assert LoginView(refreshed_browser).submit.is_enabled
    LoginView(refreshed_browser).submit.click()
    assert "Incorrect email or password. Please try again" in LoginView(refreshed_browser).error_message.text
