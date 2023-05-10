"""View representations of Email pages"""
from widgetastic.widget import TextInput

from testsuite.ui.views.admin.audience import BaseAudienceView


class SupportEmailsView(BaseAudienceView):
    """View representation of Support Emails page"""

    path_pattern = "/site/emails/edit"
    support_email = TextInput(id="account_support_email")

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.support_email.is_displayed
            and self.path in self.browser.url
        )
