"""View representations of Accounts pages"""
from widgetastic.widget import TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import AudienceNavView
from testsuite.ui.widgets import Link


# pylint: disable=abstract-method
class AccountsTable(PatternflyTable):
    """
    Table defined by 3scale in Accounts view contains two headers: classic table header and header dedicated
    to search or row manipulation. This widget specifies correct header columns. It may extend already existing
    search implementation from PF4 in the future.
    """
    HEADERS = "./thead/tr[1]/th"


class AccountsView(AudienceNavView):
    """View representation of Accounts Listing page"""
    endpoint_path = '/buyers/accounts'
    new_account = Link("//a[@href='/buyers/accounts/new']")
    table = AccountsTable("//*[@id='buyer_accounts']")

    @step("NewAccountView")
    def new(self):
        """Create new Account"""
        self.new_account.click()

    @step("AccountsDetailView")
    def detail(self, account_id):
        """Opens detail Account by ID"""
        self.table.row(_row__attr=('id', 'account_' + str(account_id))).grouporg.click()

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AudienceNavView

    def is_displayed(self):
        return AudienceNavView.is_displayed(self) and self.new_account.is_displayed and self.table.is_displayed and \
               self.endpoint_path in self.browser.url


class AccountsDetailView(AudienceNavView):
    """View representation of Account detail page"""
    endpoint_path = '/buyers/accounts/{account_id}'

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AccountsView

    def is_displayed(self):
        return AudienceNavView.is_displayed and self.endpoint_path in self.browser.url


class NewAccountView(AudienceNavView):
    """View representation of New Account page"""
    endpoint_path = '/buyers/accounts/new'

    username = TextInput(id='#account_user_username')
    email = TextInput(id='#account_user_email')
    password = TextInput(id='#account_user_password')
    organization = TextInput(id='#account_org_name')

    def prerequisite(self):
        return AccountsView

    def is_displayed(self):
        return AudienceNavView.is_displayed(self) and self.username.is_displayed and self.email.is_displayed\
               and self.organization.is_displayed and self.endpoint_path in self.browser.url
