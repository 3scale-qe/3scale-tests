"""Test of messages and mails functionality in UI"""
import pytest

from testsuite.utils import blame
from testsuite.ui.views.devel.messages import InboxView
from testsuite.ui.views.admin.audience.application import ApplicationsView


@pytest.mark.usefixtures("login", "application", "service")
def test_bulk_messages(custom_devel_login, account, navigator, request, mailhog_client):
    """
    Test:
        - Send bulk message to multiple applications
        - Assert that messages were received in developer portal
        - Assert that messages were sent via mail
    """
    subject = blame(request, "subject")
    content = blame(request, "message")
    settings = navigator.navigate(ApplicationsView)
    app_count = settings.send_email_to_all_apps(subject, content)

    custom_devel_login(account)
    messages_page = navigator.navigate(InboxView)

    assert len([msg for msg in messages_page.messages_table.read() if msg["SUBJECT"] == subject]) != 0
    # assert inside mailhog method
    mailhog_client.assert_message_received(subject=subject, expected_count=app_count)
    mailhog_client.assert_message_received(content=content, expected_count=app_count)
