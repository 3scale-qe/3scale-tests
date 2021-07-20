"""View representations of SSO Integrations pages"""
from urllib.parse import urlparse

from widgetastic.widget import TextInput, GenericLocatorWidget, View, Text
from widgetastic_patternfly4 import PatternflyTable, Button

from testsuite import settings
from testsuite.ui.navigation import step, Navigable
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import Link, ThreescaleDropdown
from testsuite.ui.widgets.buttons import ThreescaleCreateButton, ThreescaleEditButton, ThreescaleDeleteButton


class SSOIntegrationsView(BaseSettingsView):
    """View representation of SSO Integrations page"""
    path_pattern = "/p/admin/account/authentication_providers"
    new_integration = Link("//a[@href='/p/admin/account/authentication_providers/new']")
    table = PatternflyTable("//table[@class='data']")

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
        return BaseSettingsView.is_displayed.fget(self) and \
               self.path in self.browser.url and self.new_integration.is_displayed and \
               self.table.is_displayed and self.new_integration.is_displayed


class NewSSOIntegrationView(BaseSettingsView):
    """View representation of new SSO Integrations page"""
    path_pattern = "/p/admin/account/authentication_providers/new"
    SSO_provider = ThreescaleDropdown("//*[@id='authentication_provider_kind_input']")
    client = TextInput(id='authentication_provider_client_id')
    client_secret = TextInput(id='authentication_provider_client_secret')
    realm = TextInput(id='authentication_provider_site')
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
        return urlparse(self.browser.url).path.split('/')[-1]

    def prerequisite(self):
        return SSOIntegrationsView

    @property
    def is_displayed(self):
        return BaseSettingsView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.SSO_provider.is_displayed and self.client.is_displayed and self.client_secret.is_displayed \
               and self.realm.is_displayed


class SSOIntegrationDetailView(BaseSettingsView):
    """View representation of detail SSO Integrations page"""
    path_pattern = "/p/admin/account/authentication_providers/{integration_id}"
    test_flow_link = Link(".//*[normalize-space(.)='Test authentication flow now']")
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
        return BaseSettingsView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.test_flow_link.is_displayed and self.edit_button.is_displayed


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
        return BaseSettingsView.is_displayed.fget(self) and self.path in self.browser.url \
               and self.delete_button.is_displayed


class Auth0View(View, Navigable):
    """View representation of 3rd party Auth0 provider page"""
    url_domain = settings["auth0"]["domain"]
    email = TextInput(name="email")
    password = TextInput(name="password")
    login_button = GenericLocatorWidget(locator="//button[@aria-label='Log In']")
    last_login_button = GenericLocatorWidget(locator="//*[contains(@class,'auth0-lock-social-button')]")
    not_my_account = GenericLocatorWidget(locator="//*[@class='auth0-lock-alternative-link']")

    def login(self, email, password):
        """Login to 3scale via Auth0"""
        self.last_login_button.wait_displayed()
        if self.email.is_displayed:
            self.email.fill(email)
            self.password.fill(password)
            self.login_button.click()
        else:
            self.last_login_button.click()

    @property
    def is_displayed(self):
        return self.email.is_displayed and self.password.is_displayed and self.login_button.is_displayed and \
               self.url_domain in self.browser.url


class RhssoView(View, Navigable):
    """View representation of 3rd party RHSSO provider page"""
    username = TextInput(name="username")
    password = TextInput(name="password")
    login_button = GenericLocatorWidget(locator="//*[@name='login']")

    def login(self, username, password):
        """Login to 3scale via Auth0"""
        is_logged_in = BaseAdminView(self.browser.root_browser).is_displayed
        if not is_logged_in:
            self.username.wait_displayed()
            self.username.fill(username)
            self.password.fill(password)
            self.login_button.click()

    @property
    def is_displayed(self):
        return self.username.is_displayed and self.password.is_displayed and self.login_button.is_displayed
