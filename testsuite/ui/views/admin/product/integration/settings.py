"""View representations of products integration section pages"""
from widgetastic.widget import TextInput

from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import RadioGroup
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton


class ProductSettingsView(BaseProductView):
    """View representation of Product's Settings page"""
    path_pattern = "/apiconfig/services/{product_id}/settings"
    staging_url = TextInput(id="service_proxy_attributes_sandbox_endpoint")
    production_url = TextInput(id="service_proxy_attributes_endpoint")
    deployment = RadioGroup('//*[@id="service_deployment_option_input"]')
    authentication = RadioGroup('//*[@id="service_proxy_authentication_method_input"]')
    client_id = TextInput(id="service_proxy_attributes_jwt_claim_with_client_id")
    update_button = ThreescaleUpdateButton()

    def update_client_id(self, string):
        """Update client_id"""
        self.client_id.fill(string)

    def update_gateway(self, staging="", production=""):
        """Update gateway"""
        if staging:
            self.staging_url.fill(staging)
        if production:
            self.production_url.fill(production)
        self.update_button.click()

    def change_authentication(self, option):
        """Change authentication"""
        self.authentication.select(option)
        self.update_button.click()

    def change_deployment(self, option):
        """Change deployment"""
        self.deployment.select(option)
        self.update_button.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.deployment.is_displayed
