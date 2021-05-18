"""Developer portal smoke tests"""
import pytest

from testsuite import settings
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.views.devel import LandingView, BaseDevelView


# pylint: disable=unused-argument
@pytest.mark.smoke
def test_devel_from_admin(login, navigator, browser):
    """Tests if developer portal is accessible via navigation menu (Developer portal > Visit Portal)"""
    audience = navigator.navigate(BaseAudienceView)
    audience.visit_portal()
    assert settings["threescale"]["devel"]["url"] in browser.url
    assert LandingView(browser).is_displayed


# pylint: disable=unused-argument
@pytest.mark.smoke
def test_devel_login(devel_login, browser):
    """Tests simple developer portal login"""
    assert BaseDevelView(browser).is_displayed
