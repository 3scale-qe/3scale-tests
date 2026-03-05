"""Test of messages and mails functionality in UI"""

import re
import backoff
import pytest

from testsuite.ui.views.admin.audience.messages import MessagesView, ComposeMessageView
from testsuite.utils import blame
from testsuite.ui.views.devel.messages import InboxView, ComposeView
from testsuite.ui.views.admin.audience.application import ApplicationsView


def _parse_link(msg):
    body = msg["MIME"]["Parts"][1]["Body"]
    link_match = re.search(r"https?://\S+", body)
    return link_match.group(0)


@backoff.on_predicate(backoff.fibo, lambda msg: msg is None, max_time=60, max_tries=10)
def get_notification_message(sender_name, searched_link, mailhog_client):
    """Searches mailhog for a notification email triggered by a developer message.
    Finds the email notification sent to admin when a developer sends a message
    and returns the message whose parsed link matches searched_link.
    @param sender_name: name of the developer account that sent the message
    @param searched_link: expected URL from the admin messages table to match against the email link
    @param mailhog_client: mailhog client used to search for notification emails
    @return: the matching mailhog message, or None if not found within the retry limit
    """
    messages = mailhog_client.find_messages(subject=f"New message from {sender_name}")
    for msg in messages["items"]:
        if _parse_link(msg) == searched_link:
            return msg
    return None


@pytest.fixture()
def subject(request):
    """Create message subject"""
    return blame(request, "subject")


@pytest.fixture()
def content(request):
    """Create message body"""
    return blame(request, "content")


# pylint: disable=too-many-arguments
@pytest.mark.usefixtures("login", "application", "service")
def test_bulk_messages(custom_devel_login, account, navigator, mailhog_client, subject, content):
    """
    Test:
        - Send bulk message to multiple applications
        - Assert that messages were received in developer portal
        - Assert that messages were sent via mail
    """
    applications = navigator.navigate(ApplicationsView)
    app_count = applications.send_email_to_all_apps(subject, content)

    custom_devel_login(account)
    messages_page = navigator.navigate(InboxView)

    assert len([msg for msg in messages_page.messages_table.read() if msg["SUBJECT"] == subject]) != 0
    # assert inside mailhog method
    mailhog_client.assert_message_received(subject=subject, content=content, expected_count=app_count)


# pylint: disable=too-many-arguments
def test_message_from_dev_to_admin_portal(
    custom_devel_login, custom_admin_login, account, navigator, mailhog_client, subject, content
):
    """
    Test:
        - Compose new message from API developer to 3scale admin
        - Assert message was received in admin portal
        - Assert that email notification was sent
    """
    custom_devel_login(account)
    compose_msg = navigator.navigate(ComposeView)
    compose_msg.send_message(subject, content)

    custom_admin_login()
    messages = navigator.navigate(MessagesView)

    link = messages.table.row(Subject__contains=subject)[1].browser.element("./a").get_attribute("href")
    notification_message = get_notification_message(
        sender_name=account.entity_name, searched_link=link, mailhog_client=mailhog_client
    )
    assert notification_message is not None


@pytest.mark.usefixtures("login", "application", "service")
def test_message_from_admin_to_dev_portal(
    custom_devel_login, account, navigator, mailhog_client, subject, content, threescale
):
    """
    Test:
        - Compose new message from 3scale admin to API developer
        - Assert that email notification was sent
        - Assert that notification about sending message was displayed
        - Assert message was received in developer portal
    """
    compose = navigator.navigate(ComposeMessageView)
    compose.send_message(subject, content)
    assert compose.notification.string_in_flash_message("message was sent.")

    mailhog_client.assert_message_received(subject=f"[msg] {subject}", expected_count=len(threescale.accounts.list()))

    custom_devel_login(account)
    inbox = navigator.navigate(InboxView)
    assert len([msg for msg in inbox.messages_table.read() if msg["SUBJECT"] == subject]) == 1
