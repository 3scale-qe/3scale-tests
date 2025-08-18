"""View representations of Token pages"""

import enum
from typing import List

from widgetastic.widget import Text, TextInput
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.settings import BaseSettingsView
from testsuite.ui.widgets import PfCheckBoxGroup, ThreescaleDropdown
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class TokensView(BaseSettingsView):
    """View representation of Tokens page"""

    path_pattern = "/p/admin/user/access_tokens"
    add_token = Text(locator="//*[@href='/p/admin/user/access_tokens/new']")
    token_table = PatternflyTable("//*[@id='access-tokens']/table")

    @step("TokenNewView")
    def add(self):
        """Opens New Token page"""
        self.add_token.click()

    def prerequisite(self):
        return BaseSettingsView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self) and self.token_table.is_displayed and self.path in self.browser.url
        )


class Scopes(enum.Enum):
    """Tokens scopes"""

    BILLING = "access_token_scopes_finance"
    MANAGEMENT = "access_token_scopes_account_management"
    ANALYTICS = "access_token_scopes_stats"
    POLICY = "access_token_scopes_policy_registry"


class TokenNewView(BaseSettingsView):
    """View representation of New Token page"""

    path_pattern = "/p/admin/user/access_tokens/new"
    name = TextInput(id="access_token_name")
    scopes = PfCheckBoxGroup("//*[@for='access_token_scopes']/ancestor::div[@class='pf-c-form__group']")
    permissions = ThreescaleDropdown("//*[@id='access_token_permission']")
    create_button = ThreescaleSubmitButton()
    token_value = Text(".//div/dt/span[text()='Token']/ancestor::dt/following-sibling::dd")

    def create(self, name: str, scopes: List[Scopes], write: bool):
        """Create Token"""
        self.name.fill(name)
        self.scopes.check(scopes)
        if write:
            self.permissions.select_by_value("rw")
        self.create_button.click()
        # token value is present on different page which is accessible only after creating a new token
        return self.token_value.read()

    def prerequisite(self):
        return TokensView

    @property
    def is_displayed(self):
        return (
            BaseSettingsView.is_displayed.fget(self)
            and self.name.is_displayed
            and self.scopes.is_displayed
            and self.permissions.is_displayed
            and self.create_button.is_displayed
            and self.path in self.browser.url
        )
