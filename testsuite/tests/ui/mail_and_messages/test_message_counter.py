"""Test of message counters in dashboard main-section tabs"""

import pytest

from testsuite.ui.views.admin.audience.messages import MessagesView
from testsuite.ui.views.admin.foundation import DashboardView
from testsuite.ui.views.devel.messages import ComposeView


@pytest.fixture()
def setup(navigator):
    """Deletes all messages from inbox"""
    admin_messages_view = navigator.navigate(MessagesView)
    admin_messages_view.delete_all()


def _assert_dashboard_counters(navigator, message_count, unread_count):
    admin_dashboard_view = navigator.navigate(DashboardView)
    assert admin_dashboard_view.msg_count == message_count
    assert admin_dashboard_view.unread_msg_count == unread_count


def _send_message_from_devel(navigator, subject, body):
    devel_compose_view = navigator.navigate(ComposeView)
    devel_compose_view.send_message(subject, body)


# pylint: disable=too-many-arguments
@pytest.mark.disruptive  # test should be mark as disruptive because it deletes the state of inbox messages
@pytest.mark.usefixtures("login", "application", "service", "setup")
def test_message_counter(custom_devel_login, custom_admin_login, account, navigator):
    """
    Test:
        - Ensure that inbox is empty
        - Assert that messages tab in admin dashboard shows 0 messages and none unread message
        - Send two e-mails from developer to admin
        - Assert that messages tab in admin dashboard shows 2 messages and 2 unread messages
        - Read all messages
        - Assert that messages tab in admin dashboard shows 2 messages and 0 unread messages
        - Delete all messages
        - Assert that messages tab in admin dashboard shows 0 messages and 0 unread messages
    """
    custom_admin_login(account)
    _assert_dashboard_counters(navigator, 0, 0)

    custom_devel_login(account)
    _send_message_from_devel(navigator, "subject1", "body1")
    _send_message_from_devel(navigator, "subject2", "body2")

    custom_admin_login(account)
    _assert_dashboard_counters(navigator, 2, 2)

    admin_messages_view = navigator.navigate(MessagesView)
    for link in admin_messages_view.get_first_unread_msg_link_gen():
        link.click()
        navigator.navigate(MessagesView)

    _assert_dashboard_counters(navigator, 2, 0)

    admin_messages_view = navigator.navigate(MessagesView)
    admin_messages_view.delete_all()

    _assert_dashboard_counters(navigator, 0, 0)
