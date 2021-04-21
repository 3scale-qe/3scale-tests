"""View representations of Billing pages"""
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import AudienceTable


class BillingView(BaseAudienceView):
    """View representation of Accounts Listing page"""
    path_pattern = '/finance'
    table = AudienceTable("//*[@class='data']")

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return self.table.is_displayed and self.path in self.browser.url
