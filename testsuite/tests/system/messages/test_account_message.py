"""
Rewrite /spec/functional_specs/account_message_spec.rb
When sending message to a developer account, the email is send
"""

import backoff


@backoff.on_exception(backoff.fibo, AssertionError, 8, jitter=None)
def assert_message_received(mailhog, text):
    """Resilient test on presence of expected message with retry"""
    messages = mailhog.messages()
    ids = list(m["ID"] for m in messages["items"] if text in m["Content"]["Body"])
    assert len(ids) == 1, f"Expected 1 mail, found {len(ids)}"
    return ids


def test_account_will_receive_email(mailhog_client, threescale, account):
    """
    Sends a message to an account
    Assert that a corresponding email has been sent
    Delete the corresponding email after the check
    It is not possible to delete email on failed tests because
    the list returned by assert_message_received would be empty
    """
    test_message_body = f"body_test_account_will_receive_email+{account.entity['org_name']}"

    threescale.threescale_client.accounts\
        .send_message(entity_id=account.entity_id, body=test_message_body)

    ids = assert_message_received(mailhog_client, test_message_body)
    mailhog_client.delete(ids)
