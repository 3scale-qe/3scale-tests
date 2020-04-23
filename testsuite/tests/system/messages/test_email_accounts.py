"""
Rewrite spec/functional_specs/email_accounts_spec.rb
Creates account and checks, if the emails informing about the
new service subscription, new application sign-up to service and application
subscription to an app plan have been sent.

This test can not be run in parallel, emails sent because of other tests
 will result in the failure of this one

"""
import re
import time
import pytest
import yaml


@pytest.fixture(scope="module")
def mailhog_delete_all(mailhog_client):
    """Deletes all mails from mailhog"""
    mailhog_client.delete()


@pytest.fixture
def account(account):
    """Changing scope of the account fixture to be called after
    mailhog_delete_all fixture"""
    return account


@pytest.fixture
def mail_template(openshift, account) -> dict:
    """loads the mail templates and substitutes the variables"""
    openshift = openshift()
    with open("mail_templates.yml") as stream:
        yaml_string = stream.read()
        yaml_string = yaml_string.replace("<test_account>", account.entity_name) \
            .replace("<test_group>", account.entity['org_name']) \
            .replace("<threescale_superdomain>",
                     openshift.config_maps["system-environment"]["THREESCALE_SUPERDOMAIN"]) \
            .replace("<account_email_domain>", "anything.invalid") \
            .replace("<username>", "admin") \
            .replace("<tenant>", "3scale") \
            .replace("<service>", "API") \
            .replace("<aplan>", "Basic") \
            .replace("\\[", "\\[") \
            .replace("\\]", "\\]")  # replaces '\\]' with '\]'

        return yaml.safe_load(yaml_string)


# pylint: disable=unused-argument
def test_emails_after_account_creation(mailhog_delete_all, mailhog_client, account, mail_template):
    """
    Checks, if the total number of received emails is three, if lower waits for the
    email that maybe have not been send yet.
    Asserts that the 'To', 'From' and 'Return-Path' addresses match the addresses from
    the template
    Asserts that the message body and header matches on of the items in the template that
    was not already matched. (The sent emails shouldn't be identical)
    """
    messages = mailhog_client.messages()
    retries = 0
    while retries < 6 and messages['total'] < 3:
        time.sleep(10)
        messages = mailhog_client.messages()
        retries += 1

    assert messages['total'] == 3

    checked_messages = []
    for message in messages['items']:
        message_body = message["Content"]["Body"]\
            .replace("=\r\n", "").replace("\r\n", "")
        headers = message["Content"]["Headers"]

        for address_type in {"To", "From", "Return-Path"}:
            assert headers[address_type][0] == mail_template["equal_templates"][address_type], \
                f"The {address_type} address should be {mail_template['equal_templates'][address_type]} " \
                f"instead of {headers[address_type][0]}"

        is_message_valid = False
        for template in mail_template["subject_templates"].values():
            match_body = re.fullmatch(template["Body"], message_body)
            match_headers = re.fullmatch(template["Headers"], headers["X-SMTPAPI"][0])
            if match_body and match_headers and template["Body"] not in checked_messages:
                is_message_valid = True
                checked_messages.append(template["Body"])
                break

        assert is_message_valid, f"The sent email with following body: " \
                                 f"{message_body} and header: {headers['X-SMTPAPI']}" \
                                 f" does not corresponds to any template"
