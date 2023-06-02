"""Test of messages and mails functionality in UI"""
import pytest

from testsuite.utils import blame
from testsuite.config import settings
from testsuite.ui.views.devel.messages import InboxView, ComposeView
from testsuite.ui.views.admin.audience.application import ApplicationsView
from testsuite.ui.views.admin.login import ResetAdminPasswordView, LoginView


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
    applications = navigator.navigate(ApplicationsView)
    app_count = applications.send_email_to_all_apps(subject, content)

    custom_devel_login(account)
    messages_page = navigator.navigate(InboxView)

    assert len([msg for msg in messages_page.messages_table.read() if msg["SUBJECT"] == subject]) != 0
    # assert inside mailhog method
    mailhog_client.assert_message_received(subject=subject, content=content, expected_count=app_count)


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9707")
@pytest.mark.xfail
def test_admin_forgotten_password(account, browser, mailhog_client, navigator):
    """
    Test:
        - Create new user account
        - Send reset password
        -
    """
    mail = f'{account.entity_name}@example.com'

    navigator.open(LoginView, url=settings["threescale"]["admin"]["url"])
    reset_view = navigator.navigate(ResetAdminPasswordView)
    reset_view.reset_password(mail)

    mailhog_client.assert_message_received(subject="Password Recovery", receiver=mail, expected_count=1)
