"""
Rewrite /spec/functional_specs/account_message_spec.rb
When sending message to a developer account, the email is send
"""
import time


def test_account_will_receive_email(mailhog_client, threescale, account):
    """
    Sends a message to an account
    Assert that a corresponding email has been sent
    """
    test_message_body = "body_test_account_will_receive_email"

    mailhog_client.delete()

    threescale.threescale_client.accounts\
        .send_message(entity_id=account.entity_id, body=test_message_body)

    messages = mailhog_client.messages()

    contains_test_message = False
    retries = 0
    # if the email is not send within 60 seconds, fails
    while retries < 6:
        for email in messages["items"]:
            if test_message_body in email["Content"]["Body"]:
                contains_test_message = True
        if contains_test_message:
            break

        messages = mailhog_client.messages()
        time.sleep(10)
        retries += 1

    assert contains_test_message, f'The email does not not contain the ' \
                                  f'\'{test_message_body}\' in the body'
