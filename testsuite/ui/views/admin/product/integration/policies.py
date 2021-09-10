"""View representations of products integration policies section pages"""
import enum

from widgetastic.widget import TextInput, View, FileInput
from widgetastic_patternfly4 import Button

from testsuite.certificates import Certificate
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import PolicySection, ThreescaleDropdown
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


class TlsTerminationPolicyView(View):
    """
    TLS termination policy page object
    Local certificates should be uploaded from testing machine
    Embedded certificates should be already present and mounted in APIcast
    """
    NAME = "TLS Termination"
    remove_policy_btn = Button("//*[contains(@class, 'PolicyConfiguration-remove')]")
    add_cert_btn = Button(locator=".//button[contains(@class, 'btn-add')]")
    local_cert_key = FileInput(id="root_certificate_key_path")
    local_cert = FileInput(id="root_certificate_path")
    embedded_cert_path = TextInput(id="root_certificate")
    embedded_cert_key_path = TextInput(id="root_certificate_key")
    update_policy_btn = ThreescaleSubmitButton()
    cert_type_select = ThreescaleDropdown('//*[@id="root_certificates_0_anyof_select"]')

    def add_local_certs(self, mount_path):
        """Adds certs already present on APIcast"""
        self.add_cert_btn.click()
        self.cert_type_select.select_by_value("0")
        self.local_cert.fill(f"{mount_path}/tls.crt")
        self.local_cert_key.fill(f"{mount_path}/tls.key")
        self.update_policy_btn.click()

    def add_embedded_certs(self, certificate: Certificate):
        """Adds certs from filesystem"""
        self.add_cert_btn.click()
        self.cert_type_select.select_by_value("1")
        self.embedded_cert_path.fill(certificate.files["certificate"])
        self.embedded_cert_key_path.fill(certificate.files["key"])
        self.update_policy_btn.click()

    @property
    def is_displayed(self):
        return self.add_cert_btn.is_displayed


class ProductPoliciesView(BaseProductView):
    """View representation of Product's Policies page"""
    path_pattern = "/apiconfig/services/{product_id}/policies/edit"
    staging_url = TextInput(id="service_proxy_attributes_sandbox_endpoint")
    production_url = TextInput(id="service_proxy_attributes_endpoint")
    update_policy_chain_button = ThreescaleUpdateButton()
    remove_policy_btn = Button(locator="//*[contains(text(), 'Remove')]")
    policy_section = PolicySection()
    echo_policy_view = View.nested(EchoPolicyView)
    tls_termination_policy_view: TlsTerminationPolicyView = View.nested(TlsTerminationPolicyView)

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
