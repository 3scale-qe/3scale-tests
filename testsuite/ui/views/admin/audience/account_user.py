"""View representations of Account User pages"""

from widgetastic.widget import TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin import AccountsDetailView
from testsuite.ui.views.admin.foundation import AudienceNavView
from testsuite.ui.widgets.buttons import ThreescaleUpdateButton


class AccountUserView(AudienceNavView):
    """View representation of Accounts User page"""
    path_pattern = 'buyers/accounts/{account_id}/users'
    table = PatternflyTable("//*[@id='buyer_users']")

    def __init__(self, parent, account):
        super().__init__(parent, account_id=account.entity_id)

    @step("AccountUserEditView")
    def user(self, user):
        """Open account's applications"""
        self.table.row(_row__attr=('id', f'user_{user.entity_id}'))[5].click()

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AccountsDetailView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.endpoint_path in self.browser.url and self.table.is_displayed


class AccountUserEditView(AudienceNavView):
    """View representation of Accounts User Edit page"""
    path_pattern = 'buyers/accounts/{account_id}/users/{user_id}'
    username = TextInput(id="user_username")
    email = TextInput(id="user_email")
    update_button = ThreescaleUpdateButton()

    def __init__(self, parent, account, user):
        super().__init__(parent, account_id=account.entity_id, user_id=user.entity_id)

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AccountUserView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.endpoint_path in self.browser.url \
               and self.username.is_displayed and self.email.is_displayed

    def update(self, username: str = "", email: str = ""):
        """Update account user"""
        if username:
            self.username.fill(username)
        if email:
            self.email.fill(email)
        self.update_button.click()
