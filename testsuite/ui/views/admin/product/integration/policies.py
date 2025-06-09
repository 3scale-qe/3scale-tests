"""View representations of products integration policies section pages"""

import enum
from typing import Literal

from widgetastic.widget import TextInput, View, FileInput
from widgetastic_patternfly4 import Button

from testsuite.certificates import Certificate
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import PolicySection, ThreescaleDropdown
from testsuite.ui.widgets.buttons import ThreescaleButton


class Policies(enum.Enum):
    """Policies enum"""

    THREESCALE_APICAST = "3scale APIcast"

    THREESCALE_REFERRER = "3scale Referrer"
    THREESCALE_AUTH_CACHING = "3scale Auth Caching"
    HTTP_STATUS_CODE_OVERWRITE = "HTTP Status Code Overwrite"
    CAMEL_SERVICE = "Camel Service"
    # This policy should be added in the future
    # CONDITIONAL_POLICY = "Conditional Policy [Tech preview]"
    CONTENT_CACHING = "Content caching"
    PROXY_SERVICE = "Proxy Service"
    CORS_REQUEST_HANDLING = "CORS Request Handling"
    CUSTOM_METRICS = "Custom Metrics"
    ANONYMOUS_ACCESS = "Anonymous Access"
    RATE_LIMITS_HEADERS = "Rate Limits Headers"
    ECHO = "Echo"
    EDGE_LIMITING = "Edge Limiting"
    HTTP2_ENDPOINT = "HTTP2 Endpoint"
    RETRY = "Retry"
    ROUTING = "Routing"
    SOAP = "SOAP"
    RH_SSO_KEYCLOAK_ROLE_CHECK = "RH-SSO/Keycloak Role Check"
    LIQUID_CONTEXT_DEBUG = "Liquid Context Debug"
    LOGGING = "Logging"
    MAINTENANCE_MODE = "Maintenance Mode"
    OAUTH_TWO_TOKEN_INTROSPECTION = "OAuth 2.0 Token Introspection"
    UPSTREAM = "Upstream"
    UPSTREAM_CONNECTION = "Upstream Connection"
    NGINX_FILTER = "Nginx Filter"
    UPSTREAM_MUTUAL_TLS = "Upstream Mutual TLS"
    URL_REWRITING = "URL Rewriting"
    WEBSOCKET = "Websocket"
    TLS_CLIENT_CERTIFICATE_VALIDATION = "TLS Client Certificate Validation"
    TLS_TERMINATION = "TLS Termination"
    RESPONSE_REQUEST_CONTENT_LIMITS = "Response/Request content limits"
    OAUTH_TWO_MUTUAL_TLS_CLIENT_AUTHENTICATION = "OAuth 2.0 Mutual TLS Client Authentication"
    HEADER_MODIFICATION = "Header Modification"
    JWT_CLAIM_CHECK = "JWT Claim Check"
    IP_CHECK = "IP Check"
    THREESCALE_BATCHER = "3scale Batcher"
    ON_FAIL = "On fail"
    REQUEST_UNBUFFERED = "Request Unbuffered"
    URL_REWRITING_WITH_CAPTURES = "URL Rewriting with Captures"
    THE_FINANCIAL_GRADE_API = "The Financial-grade API (FAPI)"
    JWT_PARSER = "JWT Parser"


class EchoPolicyView(View):
    """Echo policy section content as nested view in ProductPoliciesView"""

    status_code_input = TextInput(id="root_status")
    exit_mode_input = TextInput(id="root_exit")
    update_policy_btn = Button(locator=".//button[text()='Update Policy']")

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
    remove_policy_btn = Button("Remove", classes=[Button.DANGER])
    add_cert_btn = Button(locator=".//button[contains(@class, 'btn-add')]")
    local_cert_key = FileInput(id="root_certificates_0_certificate_key_path")
    local_cert = FileInput(id="root_certificates_0_certificate_path")
    embedded_cert = FileInput(id="root_certificates_0_certificate")
    embedded_cert_key = FileInput(id="root_certificates_0_certificate_key")
    update_policy_btn = Button(locator=".//button[text()='Update Policy']")
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
        self.embedded_cert.fill(certificate.files["certificate"])
        self.embedded_cert_key.fill(certificate.files["key"])
        self.update_policy_btn.click()

    @property
    def is_displayed(self):
        return self.add_cert_btn.is_displayed


class URLRewritePolicyView(View):
    """URL Rewrite policy section content as nested view in ProductPoliciesView"""

    add_command_btn = Button(locator=".//fieldset[contains(@id, 'root_commands')]//button")
    add_query_args_btn = Button(locator=".//fieldset[contains(@id, 'root_query_args_commands')]//button")
    regex_input = TextInput(id="root_commands_0_regex")
    replace_input = TextInput(id="root_commands_0_replace")
    operation_select = ThreescaleDropdown('//*[@id="root_commands_0_op"]')
    update_policy_btn = Button(locator=".//button[text()='Update Policy']")

    def add_rewriting_command(self, regex, replace, operation: Literal["sub", "gsub"]):
        """Add new command to URL Rewrite policy, edit command values and update policy"""
        self.add_command_btn.click()

        self.regex_input.fill(regex)
        self.replace_input.fill(replace)

        operation_text = "Substitute the first match of the regex applied."
        if operation == "gsub":
            operation_text = "Substitute all the matches of the regex applied."
        self.operation_select.select_by_text(operation_text)

        self.update_policy_btn.click()

    @property
    def is_displayed(self):
        return self.add_command_btn.is_displayed and self.add_query_args_btn.is_displayed


class ProductPoliciesView(BaseProductView):
    """View representation of Product's Policies page"""

    path_pattern = "/apiconfig/services/{product_id}/policies/edit"
    staging_url = TextInput(id="service_proxy_attributes_sandbox_endpoint")
    production_url = TextInput(id="service_proxy_attributes_endpoint")
    update_policy_chain_button = ThreescaleButton(
        text="Update Policy Chain", classes=["pf-m-primary"], id="policies-button-sav"
    )  # type: ignore[call-arg]
    remove_policy_btn = Button(locator="//*[contains(text(), 'Remove')]")
    policy_section = PolicySection()
    echo_policy_view = View.nested(EchoPolicyView)
    tls_termination_policy_view: TlsTerminationPolicyView = View.nested(TlsTerminationPolicyView)
    url_rewrite_policy_view: URLRewritePolicyView = View.nested(URLRewritePolicyView)

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
        return (
            BaseProductView.is_displayed.fget(self)
            and self.policy_section.is_displayed
            and self.path in self.browser.url
        )
