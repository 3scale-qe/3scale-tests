"""Test of message counters in dashboard main-section tabs"""

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.utils import blame
from testsuite.ui.views.admin.audience.messages import MessagesView
from testsuite.ui.views.admin.foundation import DashboardView
from testsuite.ui.views.devel.messages import ComposeView


def assert_dashboard_counters(navigator, message_count, unread_count):
    """
    Asserts counters in the messages tab in admin dashboard
    """
    admin_dashboard_view = navigator.navigate(DashboardView)
    assert admin_dashboard_view.msg_count == message_count
    assert admin_dashboard_view.unread_msg_count == unread_count


def send_message_from_devel(navigator, subject, body):
    """
    Sends the message from the developer portal
    """
    devel_compose_view = navigator.navigate(ComposeView)
    devel_compose_view.send_message(subject, body)


@pytest.fixture()
def subjects(request):
    """Create list of message subjects"""
    return [blame(request, f"subject-{i}") for i in range(2)]


@pytest.fixture()
def contents(request):
    """Create list of message bodies"""
    return [blame(request, f"content-{i}") for i in range(2)]


# pylint: disable=too-many-arguments
@pytest.mark.skipif("TESTED_VERSION < Version('2.15')")
@pytest.mark.usefixtures("login", "application", "service")
def test_message_counter(
    custom_devel_login, custom_admin_login, account, navigator, mailhog_client, subjects, contents
):
    """
    Test:
        - Take a note of number of messages (msg_count) and unread messages (unread_count) in messages tab in
        admin dashboard
        - Send two e-mails from developer to admin
        - Assert that messages tab in admin dashboard shows msg_count + 2 messages and unread_count + 2 unread messages
        - Read two new messages
        - Assert that messages tab in admin dashboard msg_count + 2 messages and unread_count + 2 unread messages
        - Delete two new messages
        - Assert that messages tab in admin dashboard shows msg_count messages and unread_count unread messages
    """
    admin_dashboard_view = navigator.navigate(DashboardView)
    start_msg_count = admin_dashboard_view.msg_count
    start_unread_msg_count = admin_dashboard_view.unread_msg_count

    custom_devel_login(account)
    try:
        send_message_from_devel(navigator, subjects[0], contents[0])
        send_message_from_devel(navigator, subjects[1], contents[1])
    finally:
        mailhog_client.find_message(
            subject=f"New message from {account.entity_name}"
        )  # assure that messages will be deleted if skip_cleanup is false

    custom_admin_login(account)
    assert_dashboard_counters(navigator, start_msg_count + 2, start_unread_msg_count + 2)

    admin_messages_view = navigator.navigate(MessagesView)
    link = admin_messages_view.get_unread_msg_link(Subject=subjects[0], From=account.entity_name)
    link.click()
    admin_messages_view = navigator.navigate(MessagesView)
    link = admin_messages_view.get_unread_msg_link(Subject=subjects[1], From=account.entity_name)
    link.click()

    assert_dashboard_counters(navigator, start_msg_count + 2, start_unread_msg_count + 0)

    admin_messages_view = navigator.navigate(MessagesView)
    admin_messages_view.delete_message(Subject=subjects[0], From=account.entity_name)
    admin_messages_view.delete_message(Subject=subjects[1], From=account.entity_name)

    assert_dashboard_counters(navigator, start_msg_count + 0, start_unread_msg_count + 0)
