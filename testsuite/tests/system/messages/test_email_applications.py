"""Tests covering email communication based on product actions"""

import pytest

# the creation of an account triggers a one-time email to be sent; this is not affected by an upgrade
pytestmark = [pytest.mark.nopersistence]


def test_application_suspend_automatic_email(mailhog_client, account, application):
    """Test suspend application mail notification
    Sends a message to an account
    Assert that a corresponding email has been sent
    """
    account.applications.suspend(application.entity_id)
    mailhog_client.assert_message_received(
        subject="API System: Application has been suspended",
        content=f"Dear {account.entity_name},\r\n\r\n\r\nProvider Name has suspended your application for the API.",
        expected_count=1,
    )
