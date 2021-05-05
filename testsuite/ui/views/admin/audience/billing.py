"""View representations of Billing pages"""

from testsuite.ui.views.admin.foundation import AudienceNavView
from testsuite.ui.widgets import AudienceTable


class BillingView(AudienceNavView):
    """View representation of Accounts Listing page"""
    path_pattern = '/finance'
    table = AudienceTable("//*[@class='data']")

    # pylint: disable=invalid-overridden-method
    def prerequisite(self):
        return AudienceNavView

    @property
    def is_displayed(self):
        return AudienceNavView.is_displayed and self.table.is_displayed \
               and self.path in self.browser.url
