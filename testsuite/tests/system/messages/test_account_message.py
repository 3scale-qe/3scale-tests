"""
Rewrite /spec/functional_specs/account_message_spec.rb
When sending message to a developer account, the email is send
"""

import pytest


# requires mailhog *AND* special deployment with preconfigured smtp secret
@pytest.mark.sandbag
def test_account_will_receive_email(mailhog_client, threescale, account):
    """
    Sends a message to an account
    Assert that a corresponding email has been sent
    """
    test_message_body = f"body_test_account_will_receive_email+{account.entity['org_name']}"

    threescale.threescale_client.accounts.send_message(
        entity_id=account.entity_id, subject=f"test message+{account.entity['org_name']}", body=test_message_body
    )

    mailhog_client.assert_message_received(content=test_message_body)
