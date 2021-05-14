"""View representations of Accounts pages"""
from widgetastic.widget import TextInput, GenericLocatorWidget

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import Link, ThreescaleDropdown, AudienceTable, ThreescaleCheckBox
from testsuite.ui.widgets.buttons import ThreescaleCreateButton, ThreescaleUpdateButton, ThreescaleDeleteButton, \
    ThreescaleEditButton


class AccountsView(BaseAudienceView):
    """View representation of Accounts Listing page"""
    path_pattern = '/buyers/accounts'
    new_account = Link("//a[@href='/buyers/accounts/new']")
    table = AudienceTable("//*[@id='buyer_accounts']")

    @step("AccountNewView")
    def new(self):
        """Create new Account"""
        self.new_account.click()

    @step("AccountsDetailView")
    def detail(self, account):
        """Opens detail Account by ID"""
        self.table.row(_row__attr=('id', f'account_{account.entity_id}')).grouporg.click()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.new_account.is_displayed and \
               self.table.is_displayed and self.path in self.browser.url


class AccountsDetailView(BaseAudienceView):
    """View representation of Account detail page"""
    path_pattern = '/buyers/accounts/{account_id}'
    edit_button = ThreescaleEditButton()
    plan_dropdown = ThreescaleDropdown("//*[@id='account_contract_plan_id']")
    change_plan_button = GenericLocatorWidget("//*[@value='Change']")
    applications_button = Link("//*[contains(@title,'applications')]")
    users_button = Link("//*[contains(@title,'users')]")

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
        self.applications_button.click()

    @step("AccountUserView")
    def users(self):
        """Open account's users"""
        self.users_button.click()

    def prerequisite(self):
        return AccountsView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.path in self.browser.url and \
               self.edit_button.is_displayed and self.applications_button.is_displayed


class AccountNewView(BaseAudienceView):
    """View representation of New Account page"""
    path_pattern = '/buyers/accounts/new'
    username = TextInput(id='account_user_username')
    email = TextInput(id='account_user_email')
    password = TextInput(id='account_user_password')
    organization = TextInput(id='account_org_name')
    create_button = ThreescaleCreateButton()

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
        return BaseAudienceView.is_displayed.fget(self) and self.username.is_displayed and self.email.is_displayed \
               and self.organization.is_displayed and self.path in self.browser.url


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
        return BaseAudienceView.is_displayed.fget(self) and self.org_name.is_displayed \
               and self.org_name.is_displayed and self.update_button.is_displayed


class AccountApplicationsView(BaseAudienceView):
    """View representation of Account's Applications page"""
    path_pattern = "/buyers/accounts/{account_id}/applications"
    create_button = Link("//*[contains(@href,'/applications/new')]")

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
        return BaseAudienceView.is_displayed.fget(self) and self.create_button.is_displayed and \
               self.path in self.browser.url


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
        return BaseAudienceView.is_displayed.fget(self) and self.account_plans_checkbox.is_displayed and \
               self.path in self.browser.url
