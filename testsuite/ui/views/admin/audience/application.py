"""View representations of Applications pages"""

from widgetastic.widget import View, TextInput, Text, GenericLocatorWidget
from widgetastic_patternfly4 import PatternflyTable
from widgetastic_patternfly4.ouia import Select

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.views.admin.audience.account import AccountApplicationsView
from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets import AudienceTable, ThreescaleSelect, ThreescaleCheckBox
from testsuite.ui.widgets.buttons import (
    ThreescaleUpdateButton,
    ThreescaleDeleteButton,
    ThreescaleCreateButton,
    ThreescaleEditButton,
    ThreescaleSubmitButton,
)


class ApplicationsBulkEmailWindow(View):
    """Bulk emails window in on applications page"""

    sub_input = TextInput(id="send_emails_subject")
    body_input = TextInput(id="send_emails_body")
    send_btn = GenericLocatorWidget(locator='.//*[(self::button) and (normalize-space(.)="Send")]')
    number_of_applications = TextInput(id="send_emails_to")

    def send_email(self, subject=None, body=None):
        """Fill email values and send mail"""
        self.sub_input.wait_displayed(delay=0.5)
        if subject:
            self.sub_input.fill(subject)
        if body:
            self.body_input.fill(body)
        self.send_btn.click(handle_alert=True)

    @property
    def is_displayed(self):
        return self.sub_input.is_displayed and self.body_input.is_displayed


class ApplicationsView(BaseAudienceView):
    """View representation of Application Listing page"""

    path_pattern = "/p/admin/applications"
    table = AudienceTable("//*[@class='data']")
    all_app_checkbox = ThreescaleCheckBox(locator="//input[@class='select-all']")
    send_email_btn = GenericLocatorWidget(".//button[text()='Send email']")
    email_window = View.nested(ApplicationsBulkEmailWindow)

    def send_email_to_all_apps(self, subject=None, body=None):
        """Send message to all selected applications
        @param subject: message subject
        @param body: message body
        @return number of selected application (to verify correct number of messages)"""
        self.all_app_checkbox.check()
        self.send_email_btn.wait_displayed(delay=3)
        self.send_email_btn.click()
        self.email_window.wait_displayed(delay=0.5)
        # magic to get number of applications
        apps_count = int(self.email_window.number_of_applications.value.split(" ", 1)[0])
        self.email_window.send_email(subject, body)
        return apps_count

    @step("ApplicationDetailView")
    def detail(self, application):
        """Opens detail app by ID"""
        self.table.row(_row__attr=("id", f"contract_{application.entity_id}")).name.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.table.is_displayed and self.path in self.browser.url


class ApplicationDetailView(BaseProductView):
    """View representation of Application detail page"""

    path_pattern = "/p/admin/applications/{application_id}"
    edit_button = ThreescaleEditButton()
    suspend_button = Text("//*[contains(@class, 'suspend')]")
    regenerate_button = Text("//*[contains(@class, 'refresh')]")
    add_random_app_key_button = Text("//*[contains(@class, 'create_key')]")
    api_credentials_table = PatternflyTable(
        "//*[@id='keys']", column_widgets={1: Text("./span/a[contains(@class, 'delete')]")}
    )
    referer_filters_input = TextInput(id="referrer_filter")
    add_referer_filter_btn = ThreescaleSubmitButton()
    plan_dropdown = ThreescaleSelect(locator="//label[@for='cinstance_plan_id']/../div[1]")
    change_plan_button = ThreescaleSubmitButton()

    def __init__(self, parent, product, application):
        super().__init__(parent, product, application_id=application.entity_id)

    def add_referer_filter(self, filter_domain):
        """Add referer filter when referer policy is applied"""
        self.referer_filters_input.fill(filter_domain)
        self.add_referer_filter_btn.click()

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
        self.api_credentials_table.row(_row__attr=("id", f"application_key_{key}"))[1].widget.click()

    def change_plan(self, value):
        """Change application plan"""
        self.plan_dropdown.item_select(value)
        self.change_plan_button.click(handle_alert=True)

    @step("ApplicationEditView")
    def edit(self):
        """Edit application plan"""
        self.edit_button.click()

    def prerequisite(self):
        return ApplicationsView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.edit_button.is_displayed
            and self.suspend_button.is_displayed
        )


class ApplicationNewView(BaseAudienceView):
    """View representation of New Application page"""

    path_pattern = "/buyers/accounts/{account_id}/applications/new"
    username = TextInput(id="cinstance[name]")
    description = TextInput(id="cinstance[description]")
    product = Select(component_id="OUIA-Generated-Select-typeahead-1")
    app_plan = Select(component_id="OUIA-Generated-Select-typeahead-2")
    create_button = ThreescaleCreateButton()

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def create(self, username: str, description: str, plan, service):
        """Create Application"""
        self.product.item_select(service["name"])
        self.app_plan.item_select(plan["name"])
        self.username.fill(username)
        self.description.fill(description)
        self.create_button.click()

    def prerequisite(self):
        return AccountApplicationsView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.username.is_displayed
            and self.description.is_displayed
            and self.path in self.browser.url
        )


class ApplicationEditView(BaseProductView):
    """View representation of Edit Application page"""

    path_pattern = "/p/admin/applications/{application_id}/edit"
    username = TextInput(id="cinstance_name")
    description = TextInput(id="cinstance_description")
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, product, application):
        super().__init__(parent, product, application_id=application.entity_id)

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
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.username.is_displayed
            and self.description.is_displayed
            and self.path in self.browser.url
        )
