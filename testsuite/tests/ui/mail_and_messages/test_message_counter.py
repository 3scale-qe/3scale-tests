"""Test of message counters in dashboard main-section tabs"""

import pytest

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


# pylint: disable=too-many-arguments
@pytest.mark.disruptive  # test should be mark as disruptive because it deletes the state of inbox messages
@pytest.mark.usefixtures("login", "application", "service")
def test_message_counter(custom_devel_login, custom_admin_login, account, navigator):
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
    send_message_from_devel(navigator, "subject1", "body1")
    send_message_from_devel(navigator, "subject2", "body2")

    custom_admin_login(account)
    assert_dashboard_counters(navigator, start_msg_count + 2, start_unread_msg_count + 2)

    admin_messages_view = navigator.navigate(MessagesView)
    link = admin_messages_view.get_unread_msg_link(subject="subject1")
    link.click()
    admin_messages_view = navigator.navigate(MessagesView)
    link = admin_messages_view.get_unread_msg_link(subject="subject2")
    link.click()

    assert_dashboard_counters(navigator, start_msg_count + 2, start_unread_msg_count + 0)

    admin_messages_view = navigator.navigate(MessagesView)
    admin_messages_view.delete_message("subject1")
    admin_messages_view.delete_message("subject2")

    assert_dashboard_counters(navigator, start_msg_count + 0, start_unread_msg_count + 0)
