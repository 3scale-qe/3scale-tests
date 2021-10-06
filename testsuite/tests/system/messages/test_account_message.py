"""
Rewrite /spec/functional_specs/account_message_spec.rb
When sending message to a developer account, the email is send
"""

import backoff


@backoff.on_exception(backoff.fibo, AssertionError, 8, jitter=None)
def assert_message_received(mailhog, text):
    """Resilient test on presence of expected message with retry"""
    messages = mailhog.messages()
    assert any(m for m in messages["items"] if text in m["Content"]["Body"])


def test_account_will_receive_email(mailhog_client, threescale, account):
    """
    Sends a message to an account
    Assert that a corresponding email has been sent
    """
    test_message_body = "body_test_account_will_receive_email"

    mailhog_client.delete()

    threescale.threescale_client.accounts\
        .send_message(entity_id=account.entity_id, body=test_message_body)

    assert_message_received(mailhog_client, test_message_body)
