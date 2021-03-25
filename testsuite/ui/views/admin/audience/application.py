"""View representations of Applications pages"""

from widgetastic.widget import TextInput, GenericLocatorWidget
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin import AccountApplicationsView
from testsuite.ui.views.admin.foundation import AudienceNavView
from testsuite.ui.widgets import AudienceTable, Link, ThreescaleDropdown, ThreescaleUpdateButton, \
    ThreescaleDeleteButton, ThreescaleCreateButton, ThreescaleEditButton


class ApplicationsView(AudienceNavView):
    """View representation of Accounts Listing page"""
    endpoint_path = '/buyers/applications'
    table = AudienceTable("//*[@class='data']")

    @step("ApplicationDetailView")
    def detail(self, application):
        """Opens detail app by ID"""
        self.table.row(_row__attr=('id', f'contract_{application.entity_id}')).name.click()

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AudienceNavView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.table.is_displayed and self.endpoint_path in self.browser.url


class ApplicationDetailView(AudienceNavView):
    """View representation of Account detail page"""
    endpoint_path = '/apiconfig/services/{service_id}/applications/{application_id}'
    edit_button = ThreescaleEditButton()
    suspend_button = Link("//*[contains(@class, 'suspend')]")
    regenerate_button = Link("//*[contains(@class, 'refresh')]")
    add_random_app_key_button = Link("//*[contains(@class, 'create_key')]")
    api_credentials_table = PatternflyTable("//*[@id='keys']", column_widgets={
        1: Link("./span/a[contains(@class, 'delete')]")
    })
    plan_dropdown = ThreescaleDropdown("//*[@id='cinstance_plan_id']")
    change_plan_button = GenericLocatorWidget("//*[@value='Change Plan']")

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return ApplicationsView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.edit_button.is_displayed and self.suspend_button.is_displayed

    @step("ApplicationEditView")
    def edit(self):
        """Edit application plan"""
        self.edit_button.click()

    def suspend(self):
        """Suspend application plan"""
        self.suspend_button.click(handle_alert=True)

    def regenerate_user_key(self):
        """Regenerate user key"""
        self.regenerate_button.click(handle_alert=True)

    def add_random_app_key(self):
        """Add random application key"""
        self.add_random_app_key_button.click()

    def delete_app_key(self, key: str):
        """Delete given app key"""
        self.api_credentials_table.row(_row__attr=('id', f'application_key_{key}'))[1].widget.click()

    def change_plan(self, value):
        """Change application plan"""
        self.plan_dropdown.select_by_value(value)
        self.change_plan_button.click(handle_alert=True)


class ApplicationNewView(AudienceNavView):
    """View representation of New Application page"""
    endpoint_path = 'buyers/accounts/{account_id}/applications/new'
    username = TextInput(id='cinstance_name')
    email = TextInput(id='cinstance_description')
    create_button = ThreescaleCreateButton()

    def prerequisite(self):
        return AccountApplicationsView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.username.is_displayed and self.email.is_displayed \
               and self.endpoint_path in self.browser.url

    def create(self, username: str, email: str):
        """Create Application"""
        self.username.fill(username)
        self.email.fill(email)
        self.create_button.click()


class ApplicationEditView(AudienceNavView):
    """View representation of Edit Application page"""
    endpoint_path = '/apiconfig/services/{service_id}/applications/{application_id}/edit'
    username = TextInput(id='cinstance_name')
    email = TextInput(id='cinstance_description')
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def prerequisite(self):
        return ApplicationDetailView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.username.is_displayed and self.email.is_displayed \
               and self.endpoint_path in self.browser.url

    def update(self, username: str = "", email: str = ""):
        """Update Application"""
        if username:
            self.username.fill(username)
        if email:
            self.email.fill(email)
        self.update_button.click()

    def delete(self):
        """Delete Application"""
        self.delete_button.click()
