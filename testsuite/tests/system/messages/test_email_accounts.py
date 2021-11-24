"""
Rewrite spec/functional_specs/email_accounts_spec.rb
Creates account and checks, if the emails informing about the
new service subscription, new application sign-up to service and application
subscription to an app plan have been sent.
"""

import os
import re
import pytest
import yaml
import backoff


@pytest.fixture
def application(application):
    """Change the application description to avoid errors in YAML parsing
    """
    application.update({'description': 'API signup'})
    return application


@pytest.fixture
def mail_template(account, application, testconfig) -> dict:
    """loads the mail templates and substitutes the variables"""
    dirname = os.path.dirname(__file__)
    with open(f"{dirname}/mail_templates.yml", encoding="utf8") as stream:
        yaml_string = stream.read()
        yaml_string = yaml_string.replace("<test_account>", account.entity_name) \
            .replace("<test_group>", account.entity['org_name']) \
            .replace("<threescale_superdomain>", testconfig["threescale"]["superdomain"]) \
            .replace("<account_email_domain>", "anything.invalid") \
            .replace("<username>", "admin") \
            .replace("<tenant>", "3scale") \
            .replace("<service>", application['service_name']) \
            .replace("<aplan>", application['plan_name']) \
            .replace("<application>", application['name']) \
            .replace("<app_description>", application['description']) \
            .replace("\\[", "\\[") \
            .replace("\\]", "\\]")  # replaces '\\]' with '\]'

        return yaml.safe_load(yaml_string)


def matching_emails(mailhog_client, mail_template):
    """
    Checks that the 'To', 'From' and 'Return-Path' addresses match the addresses from
    the template
    Checks that the message body and header matches one of the items in the template that
    was not already matched. (The sent emails shouldn't be identical)
    Returns the ids of the matching emails
    """
    ids = []
    messages = mailhog_client.messages()
    checked_messages = []
    for message in messages['items']:
        message_body = message["Content"]["Body"]\
            .replace("=\r\n", "").replace("\r\n", "")
        headers = message["Content"]["Headers"]
        is_message_valid = False
        are_headers_valid = True
        for address_type in ["To", "From", "Return-Path"]:
            try:
                if headers[address_type][0] != mail_template["equal_templates"][address_type]:
                    are_headers_valid = False
                    break
            except KeyError:
                are_headers_valid = False
        if are_headers_valid:
            for template in mail_template["subject_templates"].values():
                match_body = re.fullmatch(template["Body"], message_body)
                match_headers = re.fullmatch(template["Headers"], headers["X-SMTPAPI"][0])
                if match_body and match_headers and template["Body"] not in checked_messages:
                    is_message_valid = True
                    checked_messages.append(template["Body"])
                    break

            if is_message_valid:
                ids.append(message["ID"])
    return ids


@pytest.fixture
def clean_up(mailhog_client, mail_template):
    """
    cleans up the emails after the test execution
    """
    yield
    ids = matching_emails(mailhog_client, mail_template)
    mailhog_client.delete(ids)


# pylint: disable=unused-argument
@backoff.on_exception(backoff.fibo, AssertionError, 8, jitter=None)
def test_emails_after_account_creation(mailhog_client, mail_template, clean_up):
    """
    Checks that the total number of matching emails is three.
    """
    ids = matching_emails(mailhog_client, mail_template)
    assert len(ids) == 3, f"Expected to find 3 emails, found {len(ids)}"
