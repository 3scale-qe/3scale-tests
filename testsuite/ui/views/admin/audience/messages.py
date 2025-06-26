"""View representations of Messages pages"""

import re

from widgetastic.widget import GenericLocatorWidget, Text, View
from widgetastic_patternfly import TextInput
from widgetastic_patternfly4 import Button, Dropdown, PatternflyTable
from widgetastic_patternfly4.ouia import Dropdown as OUIADropdown

from testsuite.ui.navigation import step
from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.views.common.foundation import FlashMessage


class MessagesView(BaseAudienceView):
    """View representation of accounts messages inbox page"""

    path_pattern = "/p/admin/messages"
    table = PatternflyTable("//table[@aria-label='Messages table']")
    compose_msg_link = GenericLocatorWidget("//*[contains(@href,'/p/admin/messages/outbox/new')]")
    empty_inbox = Text("//div[text()='Your inbox is empty, there are no new messages.']")
    select_dropdown = OUIADropdown(component_id="OUIA-Generated-Dropdown-1")
    # This dropdown does not have page unique component id
    actions_dropdown = Dropdown(
        None, locator="//div[@id='pf-random-id-0']//div[@data-ouia-component-id='OUIA-Generated-Dropdown-2']"
    )
    delete_dialog_button = Button(locator='//div[@id="colorbox"]//button[contains(text(), "Delete")]')

    def delete_all(self):
        """
        Deletes all massages from the inbox
        """
        if self.empty_inbox.is_displayed:
            return
        items = self.select_dropdown.items
        select_all_item = [s for s in items if re.match("Select all.*", s)][0]
        self.select_dropdown.item_select(select_all_item)  # item_select does not have better selector than exact text
        self.actions_dropdown.open()
        self.actions_dropdown.item_select("Delete")
        self.delete_dialog_button.wait_displayed(timeout="1s")
        self.delete_dialog_button.click()

    def delete_message(self, **kwargs):
        """
        Deletes first message with which matches given text values in columns
        e.g. delete_message(Subject='subject1, From='user1') will delete message with subject subject1 from
        user user1 if such message exists and is not already deleted.
        """
        row = self.table.row(**kwargs)
        if row.From.text != "(deleted)":
            row[4].click()

    def get_unread_msg_link(self, **kwargs):
        """Returns link to the first unread message, None if such message does not exist
        **kwargs: Allows filter rows by values in the columns.
        Keys are names of the columns, values are text values in the specified column.
        """
        return self.table.row(_row__attr=("class", "unread"), **kwargs).Subject.browser.element("./a")

    def get_first_unread_msg_link_gen(self):
        """
        Returns generator, that returns link to the first unread message until, such message exists.
        """
        while True:
            link = self.get_unread_msg_link()
            if link:
                yield link
            else:
                break

    def prerequisite(self):
        return BaseAudienceView

    @step("ComposeMessageView")
    def new_message(self):
        """Navigate to compose message view"""
        self.compose_msg_link.click()

    @property
    def is_displayed(self):
        return (
            BaseAudienceView.is_displayed.fget(self)
            and self.path in self.browser.url
            and (self.table.is_displayed or self.empty_inbox.is_displayed)
        )


class ComposeMessageView(BaseAudienceView):
    """View representation of Compose message view from admin portal do API users"""

    subject = TextInput(id="message_subject")
    body = TextInput(id="message_body")
    send_btn = Button("Send message", classes=[Button.PRIMARY])
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
