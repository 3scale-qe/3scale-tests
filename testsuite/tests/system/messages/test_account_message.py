"""
Rewrite /spec/functional_specs/account_message_spec.rb
When sending message to a developer account, the email is send
"""

import pytest

# fixture fires a one-time event that triggers an email to be sent,
# this event (sending message to account) is not affected by an upgrade
pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module")
def message_body(threescale, account):
    """
    Sends a message to an account
    """
    test_message_body = f"body_test_account_will_receive_email+{account.entity['org_name']}"

    threescale.threescale_client.accounts.send_message(
        entity_id=account.entity_id, subject=f"test message+{account.entity['org_name']}", body=test_message_body
    )
    return test_message_body


# requires mailhog *AND* special deployment with preconfigured smtp secret
@pytest.mark.sandbag
def test_account_will_receive_email(mailhog_client, message_body):
    """
    Assert that a corresponding email has been sent
    """
    mailhog_client.assert_message_received(content=message_body)
