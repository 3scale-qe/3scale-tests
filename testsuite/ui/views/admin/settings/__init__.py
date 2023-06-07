"""Essential Views for Settings Views"""
from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets.ouia import Navigation


class BaseSettingsView(BaseAdminView):
    """Parent View for Audience Views."""

    NAV_ITEMS = ["Overview", "Personal", "Users", "Integrate", "Export"]
    nav = Navigation()

    @step("@href")
    def step(self, href, **kwargs):
        """
        Perform step to specific item in Navigation with use of href locator.
        This step function is used by Navigator. Every item in Navigation Menu contains link to the specific View.
        Navigator calls this function with href parameter (Views path), Step then locates correct
        item from Navigation Menu and clicks on it.
        """
        self.nav.select_href(href, **kwargs)

    def prerequisite(self):
        return BaseAdminView

    @property
    def is_displayed(self):
        return self.nav.is_displayed and self.nav.nav_links() == self.NAV_ITEMS
