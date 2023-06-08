"""View representations of Messages pages"""
from widgetastic.widget import GenericLocatorWidget, View
from widgetastic_patternfly import TextInput
from widgetastic_patternfly4 import Button

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.views.common.foundation import FlashMessage
from testsuite.ui.widgets import AudienceTable


class MessagesView(BaseAudienceView):
    """View representation of accounts messages inbox page"""

    path_pattern = "/p/admin/messages"
    table = AudienceTable("//*[@class='data']")
    compose_msg_link = GenericLocatorWidget("//*[contains(@href,'/p/admin/messages/outbox/new')]")

    def prerequisite(self):
        return BaseAudienceView

    @step("ComposeMessageView")
    def new_message(self):
        """Navigate to compose message view"""
        self.compose_msg_link.click()

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.table.is_displayed and self.path in self.browser.url


class ComposeMessageView(BaseAudienceView):
    """View representation of Compose message view from admin portal do API users"""

    subject = TextInput(id="message_subject")
    body = TextInput(id="message_body")
    send_btn = Button("Send", classes=[Button.PRIMARY])
    notification = View.nested(FlashMessage)

    def prerequisite(self):
        return MessagesView

    def send_message(self, subject=None, body=None):
        """Send message from admin portal to API users in dev portal"""
        if subject:
            self.subject.fill(subject)
        if body:
            self.body.fill(body)
        self.send_btn.click()

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.subject.is_displayed
            and self.body.is_displayed
            and self.path in self.browser.url
        )


class SupportEmailsView(BaseAudienceView):
    """View representation of Accounts Listing page"""

    path_pattern = "/site/emails/edit"
    support_email_input = TextInput(id="account_support_email")

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.support_email_input.is_displayed
            and self.path in self.browser.url
        )
