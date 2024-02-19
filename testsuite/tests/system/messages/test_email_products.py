"""Tests covering email communication based on product actions"""

import time

import pytest

from testsuite.utils import blame

# the creation of an account triggers a one-time email to be sent; this is not affected by an upgrade
pytestmark = [pytest.mark.nopersistence]


@pytest.fixture()
def only_service(custom_service, request):
    """
    Create a custom service without backend and cleanup
    """
    return custom_service({"name": blame(request, "svc")}, proxy_params=None, backends={}, autoclean=False)


def test_service_deleted_automatic_email(mailhog_client, only_service):
    """
    Sends a message to an account
    Assert that a corresponding email has been sent
    """
    only_service.delete()
    # Deletion task scheduled to send email after 5 minutes after deletion
    time.sleep(5 * 60)

    mailhog_client.assert_message_received(subject=f"Service {only_service['name']} deleted", expected_count=1)
