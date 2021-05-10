"""View representations of Developer Portal pages"""
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import Link


class DeveloperPortalView(BaseAudienceView):
    """View representation of Accounts Listing page"""
    path_pattern = '/p/admin/cms'
    root_in_table = Link(locator='//*[@id="cms-sidebar-content"]/ul/li[1]/a')  # TODO

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.root_in_table.is_displayed and \
               self.path in self.browser.url
