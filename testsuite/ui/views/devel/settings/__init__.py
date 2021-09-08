"""Devel account settings"""
from widgetastic.widget import View, Text

from testsuite.ui.navigation import step, Navigable
from testsuite.ui.views.devel import BaseDevelView, Navbar


class SettingsTabs(View, Navigable):
    """Account settings in Devel portal"""
    ROOT = "//ul[contains(@class, 'nav-tabs')]"
    details_tab = Text("//a[@href='/admin/account']")
    users_tab = Text("//a[@href='/admin/account/users']")
    invitations_tab = Text("//a[ends-with(@href, '/invitations')]")
    invoices_tab = Text("//a[@href='/admin/account/invoices']")
    stripe_cc_tab = Text("//a[@href='/admin/account/stripe']")
    braintree_cc_tab = Text("//a[@href='/admin/account/braintree_blue']")

    @step("InvoicesView")
    def invoices(self):
        """Invoices tab"""
        self.invoices_tab.click()

    @step("StripeCCView")
    def stripe(self):
        """Stripe tab"""
        self.stripe_cc_tab.click()

    @step("BraintreeCCView")
    def braintree(self):
        """Braintree tab"""
        self.braintree_cc_tab.click()

    def prerequisite(self):
        return Navbar

    @property
    def is_displayed(self):
        return self.details_tab.is_displayed and self.users_tab.is_displayed \
                and self.invitations_tab.is_displayed and self.invoices_tab.is_displayed


class InvoicesView(BaseDevelView):
    """List of all invoices for an account"""
    path_pattern = '/admin/account/invoices'
    tabs = View.nested(SettingsTabs)

    def prerequisite(self):
        return SettingsTabs

    @property
    def is_displayed(self):
        return self.path in self.browser.url
