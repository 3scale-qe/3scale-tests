"""View representations of SSO Integrations pages for developer portal"""

from widgetastic.widget import TextInput, Text
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import ThreescaleCheckBox
from testsuite.ui.widgets.buttons import ThreescaleEditButton, ThreescaleUpdateButton


class SSOIntegrationsView(BaseAudienceView):
    """View representation of SSO Integrations page for developer portal"""

    path_pattern = "/p/admin/authentication_providers"
    table = PatternflyTable(
        "//table[@aria-label='Authentication providers table']", column_widgets={"Integration": Text("./a")}
    )

    @step("Auth0IntegrationDetailView")
    def auth0(self):
        """Open Auth0 integration"""
        self.table.row(integration__contains="Auth0").integration.widget.click()

    @step("RHSSOIntegrationDetailView")
    def rhsso(self):
        """Open RHSSO integration"""
        self.table.row(integration__contains="Red Hat Single Sign-On").integration.widget.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.path in self.browser.url and self.table.is_displayed


class RHSSOIntegrationDetailView(BaseAudienceView):
    """View representation of RHSSO Integration page"""

    path_pattern = "/p/admin/authentication_providers/{integration_id}"
    edit_button = ThreescaleEditButton()
    publish_checkbox = ThreescaleCheckBox("//*[@id='authentication_provider_published']")
    callback_url_text = Text("//dl[1]//dd[2]")

    def __init__(self, parent, integration):
        super().__init__(parent, integration_id=integration.entity_id)

    @step("RHSSOIntegrationEditView")
    def edit(self):
        """Edit RHSSO integration"""
        self.edit_button.click()

    def publish(self):
        """Publish RHSSO integration"""
        self.publish_checkbox.check()

    def callback_url(self):
        """:return callback url for RHSSO integration"""
        return self.callback_url_text.text

    def prerequisite(self):
        return SSOIntegrationsView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.edit_button.is_displayed
            and self.publish_checkbox.is_displayed
        )


class RHSSOIntegrationEditView(BaseAudienceView):
    """View representation of edit RHSSO Integration page"""

    path_pattern = "/p/admin/authentication_providers/{integration_id}/edit"
    client_id = TextInput(id="authentication_provider_client_id")
    client_secret = TextInput(id="authentication_provider_client_secret")
    realm = TextInput(id="authentication_provider_site")
    update_button = ThreescaleUpdateButton()

    def __init__(self, parent, integration):
        super().__init__(parent, integration_id=integration.entity_id)

    def edit(self, client_id, client_secret, realm):
        """Edit RHSSO integration"""
        self.client_id.fill(client_id)
        self.client_secret.fill(client_secret)
        self.realm.fill(realm)
        self.update_button.click()

    def prerequisite(self):
        return RHSSOIntegrationDetailView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.client_id.is_displayed
            and self.client_secret.is_displayed
        )


class Auth0IntegrationDetailView(BaseAudienceView):
    """View representation of Auth0 Integration page"""

    path_pattern = "/p/admin/authentication_providers/{integration_id}"
    edit_button = ThreescaleEditButton()
    publish_checkbox = ThreescaleCheckBox("//*[@id='authentication_provider_published']")
    callback_urls_text = Text("//dl[1]//dd[2]")

    def __init__(self, parent, integration):
        super().__init__(parent, integration_id=integration.entity_id)

    @step("Auth0IntegrationEditView")
    def edit(self):
        """Edit Auth0 integration"""
        self.edit_button.click()

    def publish(self):
        """Publish auth0 integration"""
        self.publish_checkbox.check()

    def callback_urls(self):
        """:return callback urls for Auth0 integrations"""
        return self.callback_urls_text.text.split(", ")

    def prerequisite(self):
        return SSOIntegrationsView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.edit_button.is_displayed
            and self.publish_checkbox.is_displayed
        )


class Auth0IntegrationEditView(BaseAudienceView):
    """View representation of edit Auth0 Integration page"""

    path_pattern = "/p/admin/authentication_providers/{integration_id}/edit"
    client_id = TextInput(id="authentication_provider_client_id")
    client_secret = TextInput(id="authentication_provider_client_secret")
    site = TextInput(id="authentication_provider_site")
    update_button = ThreescaleUpdateButton()

    def __init__(self, parent, integration):
        super().__init__(parent, integration_id=integration.entity_id)

    def edit(self, client_id, client_secret, site):
        """Edit Auth0 integration"""
        self.client_id.fill(client_id)
        self.client_secret.fill(client_secret)
        self.site.fill(site)
        self.update_button.click()

    def prerequisite(self):
        return Auth0IntegrationDetailView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.client_id.is_displayed
            and self.client_secret.is_displayed
        )
