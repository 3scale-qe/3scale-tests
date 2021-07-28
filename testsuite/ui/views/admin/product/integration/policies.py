"""View representations of products integration policies section pages"""
import enum
from widgetastic.widget import TextInput, View

from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import Link, PolicySection
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton, ThreescaleSubmitButton


class Policies(enum.Enum):
    """Policies enum"""
    THREESCALE_APICAST = "3scale APIcast"
    ECHO = "Echo"
    THREESCALE_REFERRER = "3scale Referrer"


class EchoPolicyView(View):
    """Echo policy section content as nested view in ProductPoliciesView"""
    status_code_input = TextInput(id="root_status")
    exit_mode_input = TextInput(id="root_exit")
    update_policy_btn = ThreescaleSubmitButton()

    def edit_echo_policy(self, status_code):
        """Edit values in Echo policy and update it"""
        self.status_code_input.fill(status_code)
        self.update_policy_btn.click()

    @property
    def is_displayed(self):
        return self.exit_mode_input.is_displayed and self.status_code_input.is_displayed


class ProductPoliciesView(BaseProductView):
    """View representation of Product's Policies page"""
    path_pattern = "/apiconfig/services/{product_id}/policies/edit"
    staging_url = TextInput(id="service_proxy_attributes_sandbox_endpoint")
    production_url = TextInput(id="service_proxy_attributes_endpoint")
    update_policy_chain_button = ThreescaleUpdateButton()
    remove_policy_btn = Link("//*[contains(@class, 'PolicyConfiguration-remove')]")
    policy_section = PolicySection()
    echo_policy_view = View.nested(EchoPolicyView)

    def add_policy(self, policy: Policies):
        """Add policy to policy chain by name"""
        self.policy_section.add_policy(policy)

    def remove_policy(self, policy: Policies):
        """Remove policy from policy chain by name"""
        self.policy_section.edit_policy(policy)
        self.remove_policy_btn.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return BaseProductView.is_displayed.fget(self) and self.policy_section.is_displayed and \
               self.path in self.browser.url
