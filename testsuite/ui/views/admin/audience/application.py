"""View representations of Applications pages"""

from widgetastic.widget import TextInput, GenericLocatorWidget, Text
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin import AccountApplicationsView
from testsuite.ui.views.admin.foundation import AudienceNavView
from testsuite.ui.widgets import AudienceTable, Link, ThreescaleDropdown
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton, ThreescaleDeleteButton, \
    ThreescaleCreateButton, ThreescaleEditButton


class ApplicationsView(AudienceNavView):
    """View representation of Accounts Listing page"""
    path_pattern = '/buyers/applications'
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
        return AudienceNavView.is_displayed and self.table.is_displayed and self.path in self.browser.url


class ApplicationDetailView(AudienceNavView):
    """View representation of Account detail page"""
    path_pattern = '/apiconfig/services/{product_id}/applications/{application_id}'
    edit_button = ThreescaleEditButton()
    suspend_button = Link("//*[contains(@class, 'suspend')]")
    regenerate_button = Link("//*[contains(@class, 'refresh')]")
    add_random_app_key_button = Link("//*[contains(@class, 'create_key')]")
    api_credentials_table = PatternflyTable("//*[@id='keys']", column_widgets={
        1: Link("./span/a[contains(@class, 'delete')]")
    })
    plan_dropdown = ThreescaleDropdown("//*[@id='cinstance_plan_id']")
    change_plan_button = GenericLocatorWidget("//*[@value='Change Plan']")

    def __init__(self, parent, product, application):
        super().__init__(parent, product_id=product.entity_id, application_id=application.entity_id)

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

    @step("ApplicationEditView")
    def edit(self):
        """Edit application plan"""
        self.edit_button.click()

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return ApplicationsView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.path in self.browser.url \
               and self.edit_button.is_displayed and self.suspend_button.is_displayed


class ApplicationNewView(AudienceNavView):
    """View representation of New Application page"""
    path_pattern = 'buyers/accounts/{account_id}/applications/new'
    username = TextInput(id='cinstance_name')
    description = TextInput(id='cinstance_description')
    app_plan = Text("//*[@id='select2-cinstance_plan_id-container']")
    create_button = ThreescaleCreateButton()

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def create(self, username: str, description: str, plan):
        """Create Application"""
        plan_name = plan["name"]
        if self.app_plan.text is not plan_name:
            self.app_plan.click()
            self.browser.element(f".//*[contains(text(),'{plan['name']}')]").click()
            # Since this element is totally different from patternfly 4 and
            # select options and root element are in different html trees, we need to do this 'hack' to make it work.
            self.app_plan.click()
        self.username.fill(username)
        self.description.fill(description)
        self.create_button.click()

    def prerequisite(self):
        return AccountApplicationsView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.username.is_displayed and self.description.is_displayed \
               and self.path in self.browser.url


class ApplicationEditView(AudienceNavView):
    """View representation of Edit Application page"""
    path_pattern = '/apiconfig/services/{product_id}/applications/{application_id}/edit'
    username = TextInput(id='cinstance_name')
    description = TextInput(id='cinstance_description')
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, product, application):
        super().__init__(parent, product_id=product.entity_id, application_id=application.entity_id)

    def update(self, username: str = "", description: str = ""):
        """Update Application"""
        if username:
            self.username.fill(username)
        if description:
            self.description.fill(description)
        self.update_button.click()

    def delete(self):
        """Delete Application"""
        self.delete_button.click()

    def prerequisite(self):
        return ApplicationDetailView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.username.is_displayed and self.description.is_displayed \
               and self.path in self.browser.url
