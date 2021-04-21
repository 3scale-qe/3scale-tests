"""Essential Views for Audience Views"""
from testsuite.ui.navigation import step
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.widgets import NavigationMenu


class BaseAudienceView(BaseAdminView):
    """Parent View for Audience Views."""
    NAV_ITEMS = ['Accounts', 'Applications', 'Billing', 'Developer Portal', 'Messages']
    nav = NavigationMenu(id='mainmenu')

    @step("@href")
    def step(self, href, **kwargs):
        """
        Perform step to specific item in Navigation with use of href locator.
        This step function is used by Navigator. Every item in Navigation Menu contains link to the specific View.
        Navigator calls this function with href parameter (Views endpoint_path), Step then locates correct
        item from Navigation Menu and clicks on it.
        """
        self.nav.select_href(href, **kwargs)

    def prerequisite(self):
        return BaseAdminView

    @property
    def is_displayed(self):
        if not self.nav.is_displayed:
            return False

        present_nav_items = set(self.nav.nav_links()) & set(self.NAV_ITEMS)
        return len(present_nav_items) > 3
