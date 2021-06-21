from widgetastic.widget import View

from testsuite.ui.navigation import step, Navigable
from testsuite.ui.views.devel import BaseDevelView, Navbar
from testsuite.ui.widgets import Link


class SettingsTabs(View, Navigable):
    ROOT = "//ul[contains(@class, 'nav-tabs')]"
    details_tab = Link("//a[@href='/admin/account']")
    users_tab = Link("//a[@href='/admin/account/users']")
    invitations_tab = Link("//a[ends-with(@href, '/invitations')]")
    invoices_tab = Link("//a[@href='/admin/account/invoices']")
    stripe_cc_tab = Link("//a[@href='/admin/account/stripe']")
    braintree_cc_tab = Link("//a[@href='/admin/account/braintree']")

    @step("InvoicesView")
    def invoices(self):
        self.invoices_tab.click()

    @step("StripeCCView")
    def stripe(self):
        self.stripe_cc_tab.click()

    def prerequisite(self):
        return Navbar

    @property
    def is_displayed(self):
        return self.details_tab.is_displayed and self.users_tab.is_displayed \
                and self.invitations_tab.is_displayed and self.invoices_tab.is_displayed


class InvoicesView(BaseDevelView):
    path_pattern = '/admin/account/invoices'
    tabs = View.nested(SettingsTabs)

    def prerequisite(self):
        return SettingsTabs

    @property
    def is_displayed(self):
        return self.path in self.browser.url
