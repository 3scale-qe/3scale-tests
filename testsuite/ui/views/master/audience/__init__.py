"""Essential Views for Audience Views"""
from testsuite.ui.navigation import step
from testsuite.ui.views.master.foundation import BaseMasterView
from testsuite.ui.widgets import NavigationMenu


class BaseMasterAudienceView(BaseMasterView):
    """Parent View for Audience Views."""
    NAV_ITEMS = ['Accounts', 'Applications', 'Messages']
    nav = NavigationMenu(id='mainmenu')

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
        return BaseMasterView

    @property
    def is_displayed(self):
        return BaseMasterView.is_displayed.fget(self) \
               and self.nav.is_displayed \
               and self.nav.nav_links() == self.NAV_ITEMS
