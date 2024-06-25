"""Test of messages and mails functionality in UI"""

import pytest

from testsuite.ui.views.admin.audience.messages import MessagesView, ComposeMessageView
from testsuite.utils import blame
from testsuite.ui.views.devel.messages import InboxView, ComposeView
from testsuite.ui.views.admin.audience.application import ApplicationsView


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
        - Assert that email notification was sent
        - Assert message was received in admin portal
    """
    custom_devel_login(account)
    compose_msg = navigator.navigate(ComposeView)
    compose_msg.send_message(subject, content)

    mailhog_client.assert_message_received(subject=f"New message from {account.entity_name}", expected_count=1)

    custom_admin_login()
    messages = navigator.navigate(MessagesView)
    assert messages.table.row(subject__contains=subject).subject.text == subject


@pytest.mark.usefixtures("login", "application", "service")
def test_message_from_admin_to_dev_portal(
    custom_devel_login, account, navigator, mailhog_client, subject, content, threescale
):
    """
    Test:
        - Compose new message from 3scale admin to API developer
        - Assert that email notification was sent
        - Assert that notification about sending message was displyed
        - Assert message was received in developer portal
    """
    compose = navigator.navigate(ComposeMessageView)
    compose.send_message(subject, content)
    assert compose.notification.string_in_flash_message("message was sent.")

    mailhog_client.assert_message_received(subject=f"[msg] {subject}", expected_count=len(threescale.accounts.list()))

    custom_devel_login(account)
    inbox = navigator.navigate(InboxView)
    assert len([msg for msg in inbox.messages_table.read() if msg["SUBJECT"] == subject]) == 1
