"""Developer portal smoke tests"""
import pytest

from testsuite import settings
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.views.devel import BaseDevelView, AccessView, LandingView


@pytest.fixture(scope="module")
def provider_account(provider_account):
    """Fixture returns Provider account.
    If `site_access_code` was changed in tests, it is restored to its original value"""
    access_code = provider_account['site_access_code']
    yield provider_account
    provider_account.update({"site_access_code": access_code})


# pylint: disable=unused-argument
@pytest.mark.smoke
def test_devel_from_admin(login, navigator, browser):
    """Tests if developer portal is accessible via navigation menu (Developer portal > Visit Portal)"""
    audience = navigator.navigate(BaseAudienceView)
    with browser.new_tab(audience.visit_portal):
        assert settings["threescale"]["devel"]["url"] in browser.url
        view = LandingView(browser)
        view.post_navigate()
        assert view.is_displayed


# pylint: disable=unused-argument
@pytest.mark.smoke
def test_devel_login(devel_login, browser):
    """Tests simple developer portal login"""
    assert BaseDevelView(browser).is_displayed


@pytest.mark.smoke
def test_empty_access_code(browser, provider_account):
    """Test developer portal accessibility when `site_access_code` is empty"""
    browser.selenium.delete_all_cookies()
    browser.url = settings["threescale"]["devel"]["url"]
    assert AccessView(browser).is_displayed

    provider_account.update({"site_access_code": ""})
    browser.selenium.refresh()
    assert LandingView(browser).is_displayed
