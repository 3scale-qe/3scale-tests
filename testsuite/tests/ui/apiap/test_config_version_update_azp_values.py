"""
"https://issues.redhat.com/browse/THREESCALE-6468"
"""

import pytest

from testsuite.ui.views.admin.product.integration.configuration import ProductConfigurationView
from testsuite.ui.views.admin.product.integration.settings import ProductSettingsView


@pytest.mark.usefixtures("login")
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6468")
def test_config_version(service, navigator):
    """
    Test:
        - Navigates to Product Settings view
        - Changes authentication to OpenID, updates Product
        - Navigates to Product Configuration
        - Assert that there is notification for outdated config
        - Assert that promote button is enabled
        - Promotes to staging
        - Navigates to Product Settings view
        - Changes default ClientID value "azp", updates Product
        - Assert that the desired value saved to configuration
        - Navigates to Product Configuration
        - Assert that the promote button is disabled
        - Assert that there isn't notification for outdated config
    """
    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.change_authentication("service_proxy_authentication_method_oidc")
    settings = navigator.navigate(ProductConfigurationView, product=service)

    assert settings.outdated_config.is_enabled
    assert settings.configuration.staging_promote_btn.is_displayed
    settings.configuration.staging_promote_btn.click()

    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.update_client_id("azpza")
    settings.update_button.click()
    assert settings.client_id.value == "azpza"

    settings = navigator.navigate(ProductConfigurationView, product=service)
    assert settings.configuration.staging_promote_btn.is_enabled
    assert settings.outdated_config.is_displayed

    assert service.proxy.list().configs.latest().entity["content"]["proxy"]["authentication_method"]
