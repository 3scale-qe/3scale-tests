"""Essential Views for Audience Views"""
from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets import NavigationMenu


class BaseAudienceView(BaseAdminView):
    """Parent View for Audience Views."""
    NAV_ITEMS = ['Accounts', 'Applications', 'Billing', 'Developer Portal', 'Messages']
    nav = NavigationMenu(id='mainmenu')

    def visit_portal(self):
        """
        Directly visit Devel portal - opens new tab with Devel portal!
        The same could be done with step function and href argument that would contain Devel portal url or access_code.
        This method provides simple solution that does not need any information mentioned above.
        """
        self.nav.select("Developer Portal", "Visit Portal")

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
