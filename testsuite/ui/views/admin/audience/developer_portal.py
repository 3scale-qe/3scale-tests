"""View representations of Developer Portal pages"""

from testsuite.ui.views.admin.foundation import AudienceNavView
from testsuite.ui.widgets import Link


class DeveloperPortalView(AudienceNavView):
    """View representation of Accounts Listing page"""
    endpoint_path = '/p/admin/cms'
    root_in_table = Link(locator='//*[@id="cms-sidebar-content"]/ul/li[1]/a')  # TODO

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AudienceNavView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.root_in_table.is_displayed \
               and self.endpoint_path in self.browser.url
