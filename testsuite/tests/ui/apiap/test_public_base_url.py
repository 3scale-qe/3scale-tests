"""Test for Public Base URLs as localhost"""
import pytest
from widgetastic.widget import Text

from testsuite.ui.views.admin.product.integration.settings import ProductSettingsView

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7149"),
    pytest.mark.require_version("2.12")
]


# pylint: disable=unused-argument
def test_public_base_url(login, navigator, service, browser):
    """
    Test:
        - navigate to Product settings page
        - try to set staging and production Public Base URLs to localhost
        - assert that it's not possible
    """
    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.update_gateway(staging='https://localhost:80', production='https://localhost:80')

    staging = Text(browser, '//*[@id="service_proxy_attributes_sandbox_endpoint_input"]/p[2]')
    production = Text(browser, '//*[@id="service_proxy_attributes_endpoint_input"]/p[2]')

    assert staging.text == "can't be localhost"
    assert production.text == "can't be localhost"
