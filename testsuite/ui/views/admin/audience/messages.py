"""View representations of Messages pages"""
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import AudienceTable


class MessagesView(BaseAudienceView):
    """View representation of Accounts Listing page"""
    path_pattern = '/p/admin/messages'
    table = AudienceTable("//*[@class='data']")

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.table.is_displayed and self.path in self.browser.url
