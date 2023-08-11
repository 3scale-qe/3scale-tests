"""View representations of SSO Integrations pages"""
from urllib.parse import urlparse

from widgetastic.widget import TextInput, Text
from widgetastic_patternfly4 import PatternflyTable, Button

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import ThreescaleDropdown, ThreescaleCheckBox
from testsuite.ui.widgets.buttons import ThreescaleCreateButton, ThreescaleEditButton, ThreescaleDeleteButton


class SSOIntegrationsView(BaseSettingsView):
    """View representation of SSO Integrations page"""

    path_pattern = "/p/admin/account/authentication_providers"
    new_integration = Text("//a[@href='/p/admin/account/authentication_providers/new']")
    table = PatternflyTable("//table[@aria-label='Authentication providers table']")

    @step("NewSSOIntegrationView")
    def new(self):
        """New SSO integration"""
        self.new_integration.click()

    @step("SSOIntegrationDetailView")
    def detail(self):
        """
        Detail of SSO integration
        https://issues.redhat.com/browse/THREESCALE-7113
        Due to this issue and lack of unique html attributes for each row we need to use this workaround.
        """
        list(self.table.rows())[-1].integration.click()

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.new_integration.is_displayed
            and self.table.is_displayed
            and self.new_integration.is_displayed
        )


class NewSSOIntegrationView(BaseSettingsView):
    """View representation of new SSO Integrations page"""

    path_pattern = "/p/admin/account/authentication_providers/new"
    SSO_provider = ThreescaleDropdown("//*[@id='authentication_provider_kind_input']")
    client = TextInput(id="authentication_provider_client_id")
    client_secret = TextInput(id="authentication_provider_client_secret")
    realm = TextInput(id="authentication_provider_site")
    create_button = ThreescaleCreateButton()

    def create(self, provider, client, secret, realm=None):
        """Create SSO integration"""
        self.SSO_provider.select_by_value(provider)
        self.client.fill(client)
        self.client_secret.fill(secret)
        if realm:
            self.realm.fill(realm)
        self.create_button.click()
        return self.get_id()

    def get_id(self):
        """Get ID of SSO integration from URL"""
        return urlparse(self.browser.url).path.split("/")[-1]

    def prerequisite(self):
        return SSOIntegrationsView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.SSO_provider.is_displayed
            and self.client.is_displayed
            and self.client_secret.is_displayed
            and self.realm.is_displayed
        )


class SSOIntegrationDetailView(BaseSettingsView):
    """View representation of detail SSO Integrations page"""

    path_pattern = "/p/admin/account/authentication_providers/{integration_id}"
    test_flow_link = Text(".//*[normalize-space(.)='Test authentication flow now']")
    test_flow_checkbox = ThreescaleCheckBox(locator="//input[@id='check']")
    callback_url = Text("//dl[2]//*[2]")
    callback_url_for_flow_test = Text("//dl[2]//*[4]")
    edit_button = ThreescaleEditButton()
    publish_button = Button(locator="//input[@value='Publish']")

    def __init__(self, parent, integration):
        super().__init__(parent, integration_id=integration.entity_id)

    def callback_urls(self):
        """Return callbacks url of SSO integration"""
        return [self.callback_url.text, self.callback_url_for_flow_test.text]

    def publish(self):
        """Publish SSO integration"""
        self.publish_button.wait_displayed()
        self.publish_button.click()

    @step("SSOIntegrationEditView")
    def edit(self):
        """Edit SSO integration"""
        self.edit_button.click()

    def test_flow(self, provider_type, email, password):
        """Test authentication flow"""
        self.test_flow_link.click()
        provider = provider_type(self.browser.root_browser)
        provider.login(email, password)

    def prerequisite(self):
        return SSOIntegrationsView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.test_flow_link.is_displayed
            and self.edit_button.is_displayed
        )


class SSOIntegrationEditView(BaseSettingsView):
    """View representation of edit SSO Integrations page"""

    path_pattern = "/p/admin/account/authentication_providers/{integration_id}/edit"
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, integration):
        super().__init__(parent, integration_id=integration.entity_id)

    def delete(self):
        """Delete SSO integration"""
        self.delete_button.click()

    def prerequisite(self):
        return SSOIntegrationDetailView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.delete_button.is_displayed
        )
