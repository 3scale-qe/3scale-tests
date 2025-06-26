"""Devel messages pages and tabs"""

from widgetastic.widget import Text, TextInput, View
from widgetastic_patternfly4 import PatternflyTable

from testsuite.ui.navigation import Navigable, step
from testsuite.ui.views.devel import BaseDevelView, Navbar
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class MessagesTabs(View, Navigable):
    """Messages tabs in dev portal"""

    ROOT = "//ul[contains(@class, 'nav-tabs')]"
    compose_tab = Text("//a[contains(@href,'admin/messages/new')]")
    inbox_tab = Text("//a[contains(@href,'admin/messages/received')]")
    sent_tab = Text("//a[contains(@href,'admin/messages/sent')]")
    trash_tab = Text("//a[contains(@href,'admin/messages/trash')]")

    @step("InboxView")
    def inbox(self):
        """Inbox tab"""
        self.inbox_tab.click()

    @step("ComposeView")
    def compose(self):
        """Compose tab"""
        self.compose_tab.click()

    def prerequisite(self):
        return Navbar

    @property
    def is_displayed(self):
        return (
            self.compose_tab.is_displayed
            and self.inbox_tab.is_displayed
            and self.sent_tab.is_displayed
            and self.trash_tab.is_displayed
        )


class InboxView(BaseDevelView):
    """Dev account inbox view"""

    path_pattern = "/admin/messages/received"
    messages_table = PatternflyTable(".//table[@class='table panel panel-default']")

    def prerequisite(self):
        return MessagesTabs

    @property
    def is_displayed(self):
        return self.path in self.browser.url


class ComposeView(BaseDevelView):
    """New messages from dev portal account view"""

    path_pattern = "/admin/messages/received"
    sub_input = TextInput(id="message_subject")
    body_input = TextInput(id="message_body")
    send_btn = ThreescaleSubmitButton()

    def send_message(self, subject, body):
        """Fill message values and send mail"""
        self.sub_input.wait_displayed(delay=0.5)
        if subject:
            self.sub_input.fill(subject)
        if body:
            self.body_input.fill(body)
        self.send_btn.click()

    def prerequisite(self):
        return MessagesTabs

    @property
    def is_displayed(self):
        return self.sub_input.is_displayed and self.body_input.is_displayed and self.path in self.browser.url
