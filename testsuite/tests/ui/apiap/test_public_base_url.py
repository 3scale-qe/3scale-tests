"""Test for Public Base URLs as localhost"""

import pytest
from packaging.version import Version
from widgetastic.widget import Text

from testsuite import TESTED_VERSION
from testsuite.ui.views.admin.product.integration.settings import ProductSettingsView

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7149"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.12"), reason="TESTED_VERSION < Version('2.12')"),
]


@pytest.mark.usefixtures("login")
def test_public_base_url(navigator, service, browser):
    """
    Test:
        - navigate to Product settings page
        - try to set staging and production Public Base URLs to localhost
        - assert that it's not possible
    """
    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.update_gateway(staging="https://localhost:80", production="https://localhost:80")

    staging_error = Text(
        browser, '//*[@id="service_proxy_attributes_sandbox_endpoint_input"]/p[@class="inline-errors"]'
    )
    production_error = Text(browser, '//*[@id="service_proxy_attributes_endpoint_input"]/p[@class="inline-errors"]')

    assert staging_error.text == "can't be localhost"
    assert production_error.text == "can't be localhost"
