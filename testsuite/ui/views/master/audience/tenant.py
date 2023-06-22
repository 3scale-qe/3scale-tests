"""View representations of Tenants pages"""
from widgetastic.widget import TextInput, Text

from testsuite.ui.navigation import step
from testsuite.ui.views.master.audience import BaseMasterAudienceView
from testsuite.ui.widgets import AudienceTable
from testsuite.ui.widgets.buttons import (
    Button,
    ThreescaleDeleteButton,
    ThreescaleEditButton,
    ThreescaleSubmitButton,
    ThreescaleSearchButton,
    ThreescaleUpdateButton,
)


class TenantsView(BaseMasterAudienceView):
    """View representation of Tenants Listing page"""

    # TODO search will be separated into the AudienceTable Widget later.
    path_pattern = "/buyers/accounts"
    new_account = Text("//a[@href='/p/admin/accounts/new']")
    tenants_table = AudienceTable(
        "//*[@id='buyer_accounts']",
        column_widgets={"Group/Org.": Text("./a"), 5: Text("./ul/li/a[contains(@class, 'actions')]")},
    )
    search_button = ThreescaleSearchButton()
    search_bar = TextInput(id="search_query")

    def impersonate(self, account):
        """Impersonate tenant and switch browser context to new tab"""
        self.tenants_table.row(_row__attr=("id", f"account_{account.entity_id}"))[5].click()
        self.parent_browser.switch_to_window(self.parent_browser.window_handles[-1])

    def search(self, value: str):
        """Search in Tenant table by given value"""
        self.search_bar.fill(value)
        self.search_button.click()

    @step("TenantNewView")
    def new(self):
        """Create new Tenant"""
        self.new_account.click()

    @step("TenantDetailView")
    def detail(self, account):
        """Opens detail Account by ID"""
        self.tenants_table.row(_row__attr=("id", f"account_{account.entity_id}")).grouporg.widget.click()

    def prerequisite(self):
        return BaseMasterAudienceView

    @property
    def is_displayed(self):
        return (
            BaseMasterAudienceView.is_displayed.fget(self)
            and self.new_account.is_displayed
            and self.tenants_table.is_displayed
            and self.path in self.browser.url
        )


class TenantDetailView(BaseMasterAudienceView):
    """View representation of Tenant detail page"""

    path_pattern = "/buyers/accounts/{account_id}"
    edit_button = ThreescaleEditButton()
    applications_button = Text("//*[contains(@title,'applications')]")
    public_domain = Text(".//th[contains(text(),'Public domain')]/parent::*/td/a")
    admin_domain = Text(".//th[contains(text(),'Admin domain')]/parent::*/td/a")
    resume_b = Button("Resume", classes=["button-to", "resume"])
    suspend_b = Button("Suspend", classes=["button-to", "suspend"])
    impersonate_b = Text(".//a[contains(@href,'impersonation')]")

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    @step("TenantEditView")
    def edit(self):
        """Edit account"""
        self.edit_button.click()

    def suspend(self):
        """Suspends the tenant"""
        if self.suspend_b.is_displayed:
            self.suspend_b.click(handle_alert=True)

    def resume(self):
        """Resumes the tenant from deletion / suspension"""
        if self.resume_b.is_displayed:
            self.resume_b.click(handle_alert=True)

    def open_public_domain(self):
        """a helper function to open public-domain"""
        self.public_domain.click()

    def open_admin_domain(self):
        """a helper function to open admin-portal"""
        self.admin_domain.click()

    def impersonate(self):
        """Impersonates the tenant - gets into admin portal of tenant already logged in"""
        self.impersonate_b.click()

    def prerequisite(self):
        return TenantsView

    @property
    def is_displayed(self):
        return (
            self.path in self.browser.url
            and self.applications_button.is_displayed
            and self.admin_domain.is_displayed
            and self.public_domain.is_displayed
        )


class TenantNewView(BaseMasterAudienceView):
    """View representation of New Tenant page"""

    path_pattern = "/p/admin/accounts/new"
    password_confirm = TextInput(id="account_user_password_confirmation")
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
        self.password_confirm.fill(password)
        self.create_button.click()

    def prerequisite(self):
        return TenantsView

    @property
    def is_displayed(self):
        return (
            BaseMasterAudienceView.is_displayed.fget(self)
            and self.password_confirm.is_displayed
            and self.username.is_displayed
            and self.email.is_displayed
            and self.organization.is_displayed
            and self.path in self.browser.url
        )


class TenantEditView(BaseMasterAudienceView):
    """View representation of Edit Tenant page"""

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
        return TenantDetailView

    @property
    def is_displayed(self):
        return (
            BaseMasterAudienceView.is_displayed.fget(self)
            and self.org_name.is_displayed
            and self.org_name.is_displayed
            and self.update_button.is_displayed
        )
