"""View representations of Accounts pages"""

from widgetastic.widget import TextInput, GenericLocatorWidget, Text, View
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.views.common.foundation import FlashMessage
from testsuite.ui.widgets import (
    ThreescaleDropdown,
    AudienceTable,
    ThreescaleCheckBox,
    CheckBoxGroup,
    HorizontalNavigation,
)
from testsuite.ui.widgets.buttons import (
    ThreescaleUpdateButton,
    ThreescaleDeleteButton,
    ThreescaleEditButton,
    ThreescaleSubmitButton,
    ThreescaleSearchButton,
)


class AccountsView(BaseAudienceView):
    """View representation of Accounts Listing page"""

    # TODO search will be separated into the AudienceTable Widget later.
    path_pattern = "/buyers/accounts"
    new_account = Text("//a[@href='/buyers/accounts/new']")
    table = AudienceTable("//*[@id='buyer_accounts']", column_widgets={"Group/Org.": Text("./a")})
    search_button = ThreescaleSearchButton()
    search_bar = TextInput(id="search_query")

    def search(self, value: str):
        """Search in account table by given value"""
        self.search_bar.fill(value)
        self.search_button.click()

    @step("AccountNewView")
    def new(self):
        """Create new Account"""
        self.new_account.click()

    @step("AccountsDetailView")
    def detail(self, account):
        """Opens detail Account by ID"""
        self.table.row(_row__attr=("id", f"account_{account.entity_id}")).grouporg.widget.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.new_account.is_displayed
            and self.table.is_displayed
            and self.path in self.browser.url
        )


class AccountsDetailView(BaseAudienceView):
    """View representation of Account detail page"""

    path_pattern = "/buyers/accounts/{account_id}"
    edit_button = ThreescaleEditButton()
    plan_dropdown = ThreescaleDropdown("//*[@id='account_contract_plan_id']")
    change_plan_button = GenericLocatorWidget("//*[@value='Change']")
    account_navigation = HorizontalNavigation()

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def change_plan(self, value):
        """Change account plan"""
        self.plan_dropdown.select_by_value(value)
        self.change_plan_button.click(handle_alert=True)

    @step("AccountEditView")
    def edit(self):
        """Edit account"""
        self.edit_button.click()

    @step("AccountApplicationsView")
    def applications(self):
        """Open account's applications"""
        self.account_navigation.select("Application")

    @step("AccountUserView")
    def users(self):
        """Open account's users"""
        self.account_navigation.select("User")

    @step("AccountUserGroupView")
    def group(self):
        """Open account's groups"""
        self.account_navigation.select("Group Memberships")

    @step("AccountInvoicesView")
    def invoices(self):
        """Open account's users"""
        self.account_navigation.select("Invoices")

    @step("AccountInvitationsView")
    def invitations(self):
        """Open account's invitation"""
        self.account_navigation.select("Invitations")

    def prerequisite(self):
        return AccountsView

    @property
    def is_displayed(self):
        return self.path in self.browser.url and self.edit_button.is_displayed and self.account_navigation.is_displayed


class AccountNewView(BaseAudienceView):
    """View representation of New Account page"""

    path_pattern = "/buyers/accounts/new"
    username = TextInput(id="account_user_username")
    email = TextInput(id="account_user_email")
    password = TextInput(id="account_user_password")
    organization = TextInput(id="account_org_name")
    create_button = ThreescaleSubmitButton()

    def create(self, username: str, email: str, password: str, organization: str):
        """Crate new account"""
        self.username.fill(username)
        self.email.fill(email)
        self.password.fill(password)
        self.organization.fill(organization)
        self.create_button.click()

    def prerequisite(self):
        return AccountsView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and self.username.is_displayed
            and self.email.is_displayed
            and self.organization.is_displayed
        )


class AccountEditView(BaseAudienceView):
    """View representation of Edit Account page"""

    path_pattern = "/buyers/accounts/{account_id}/edit"
    org_name = TextInput(id="account_org_name")
    update_button = ThreescaleUpdateButton()
    delete_button = ThreescaleDeleteButton()

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def update(self, org_name: str):
        """Update account"""
        self.org_name.fill(org_name)
        self.update_button.click()

    def delete(self):
        """Delete account"""
        self.delete_button.click()

    def prerequisite(self):
        return AccountsDetailView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.org_name.is_displayed
            and self.org_name.is_displayed
            and self.update_button.is_displayed
        )


class AccountApplicationsView(BaseAudienceView):
    """View representation of Account's Applications page"""

    path_pattern = "/buyers/accounts/{account_id}/applications"
    create_button = Text("//*[contains(@href,'/applications/new')]")

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    @step("ApplicationNewView")
    def new(self):
        """Crate new application"""
        self.create_button.click()

    def prerequisite(self):
        return AccountsDetailView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.create_button.is_displayed
            and self.path in self.browser.url
        )


class AccountInvoicesView(BaseAudienceView):
    """View representation of Account's Invoices page"""

    path_pattern = "/buyers/accounts/{account_id}/invoices"
    create_button = Text(".action.new")
    table = PatternflyTable(".data")

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def create(self):
        """
        Creates new invoice
        Note: It creates new open invoice, without any form with random ID
        """
        self.create_button.click()

    @step("InvoiceDetailView")
    def edit(self, invoice):
        """Opens edit view for the invoice"""
        self.table.row(_row__attr=("id", f"invoice_{invoice.entity_id}")).id.click()

    def prerequisite(self):
        return AccountsDetailView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.create_button.is_displayed
            and self.path in self.browser.url
        )


class AccountInvitationsView(BaseAudienceView):
    """View representation of Account's invitation page"""

    path_pattern = "/buyers/accounts/{account_id}/invitations"
    invite_link = Text(".action.add")

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    @step("AccountInvitationNewView")
    def invite(self):
        """Invite new user"""
        self.invite_link.click()

    def prerequisite(self):
        return AccountsDetailView

    @property
    def is_displayed(self):
        return self.invite_link.is_displayed and self.path in self.browser.url


class AccountInvitationNewView(BaseAudienceView):
    """View representation of Account's new invitation page"""

    path_pattern = "/buyers/accounts/{account_id}/invitations/new"
    invite_email = TextInput(id="invitation_email")
    send_button = ThreescaleSubmitButton()

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def invite_user(self, email):
        """Invites new user by email"""
        self.invite_email.fill(email)
        self.send_button.click()

    def prerequisite(self):
        return AccountInvitationsView

    @property
    def is_displayed(self):
        return self.invite_email.is_displayed and self.send_button.is_displayed and self.path in self.browser.url


class LineItemForm(View):
    """Nested view for a Line add form"""

    path_pattern = "/buyers/accounts/{account_id}/invoices/{invoice_id}"
    ROOT = "//div[@id='colorbox']"
    name_input = TextInput("line_item[name]")
    quantity_input = TextInput("line_item[quantity]")
    description_input = TextInput("line_item[description]")
    cost_input = TextInput("line_item[cost]")
    submit = Text("//input[@type='submit']")

    def add_item(self, name, quantity, cost, description):
        """Adds item to an invoice"""
        self.name_input.fill(name)
        self.quantity_input.fill(quantity)
        self.description_input.fill(description)
        self.cost_input.fill(cost)
        self.submit.click()


class InvoiceDetailView(BaseAudienceView):
    """Invoice Detail page"""

    path_pattern = "/buyers/accounts/{account_id}/invoices/{invoice_id}"
    issue_button = Text("//form[contains(@action, 'issue.js')]/button")
    charge_button = Text("//form[contains(@action, 'charge.js')]/button")
    id_field = Text("#field-friendly_id")
    state_field = Text("#field-state")
    notification = View.nested(FlashMessage)

    # Selector which we can use to check if the charge has finished
    paid_field = Text("//td[@id='field-state' and text()='Paid']")
    add_item_btn = GenericLocatorWidget("//a[contains(@class,'action add')]")
    line_item_form = View.nested(LineItemForm)

    def __init__(self, parent, account, invoice):
        super().__init__(parent, account_id=account.entity_id, invoice_id=invoice.entity_id)
        self.invoice = invoice

    def add_items(self, items):
        """Adds item to an invoice"""
        self.add_item_btn.click()
        self.line_item_form.wait_displayed()
        for item in items:
            self.line_item_form.add_item(**item)

    def issue(self):
        """Issues the invoices (OPEN -> PENDING)"""
        self.issue_button.click(handle_alert=True)

    def charge(self):
        """Charges the invoices (PENDING -> PAID)"""
        # Charge button has two alerts which completely messed up with widgetastic.
        # https://issues.redhat.com/browse/THREESCALE-7276
        self.browser.click(self.charge_button, ignore_ajax=True)
        self.browser.handle_double_alert()

        # Wait until charge is done
        self.browser.wait_for_element(self.paid_field, timeout=5)

    def assert_issued(self):
        """Assert that invoice was correctly issued"""
        assert self.notification.is_displayed, "No notification was displayed after issuing an invoice."
        assert self.notification.string_in_flash_message("invoice issued."), "Issuing the invoice through UI failed"
        assert self.charge_button.wait_displayed, "Issuing the invoice through UI failed"

    def prerequisite(self):
        return AccountInvoicesView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.id_field.is_displayed
            and (self.issue_button.is_displayed or self.charge_button.wait_displayed)
            and self.path in self.browser.url
        )


class UsageRulesView(BaseAudienceView):
    """View representation of Account's Usage Rules page"""

    path_pattern = "/site/usage_rules/edit"
    account_plans_checkbox = ThreescaleCheckBox(locator="//input[@id='settings_account_plans_ui_visible']")
    update_button = ThreescaleUpdateButton()

    def account_plans(self):
        """Allow account plans"""
        self.account_plans_checkbox.check()
        self.update_button.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.account_plans_checkbox.is_displayed
            and self.path in self.browser.url
        )


class AccountUserGroupView(BaseAudienceView):
    """View representation of Accounts User page"""

    path_pattern = "/buyers/accounts/{account_id}/groups"
    groups = CheckBoxGroup(locator="//*[@id='account_groups_input']")
    submit = ThreescaleSubmitButton()

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    def update(self, options: list):
        """Update account group section"""
        self.groups.check_by_text(options)
        self.submit.click()

    def prerequisite(self):
        return AccountsDetailView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.groups.is_displayed and self.path in self.browser.url
