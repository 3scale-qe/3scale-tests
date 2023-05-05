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

from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Application bound to the account and service with specific description that don't break yaml parsing"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(
        rawobj.Application(blame(request, "app"), plan, "Api signup"), hooks=lifecycle_hooks,
        annotate=False)
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def mail_template(account, application, testconfig) -> dict:
    """Loads the mail templates and substitutes the variables"""
    dirname = os.path.dirname(__file__)
    with open(f"{dirname}/mail_templates.yml", encoding="utf8") as stream:
        account_email_domain = [i["email"] for i in account.users.list() if i["role"] == "admin"][0].split("@", 1)[1]
        yaml_string = stream.read()
        yaml_string = yaml_string.replace("<test_account>", account.entity_name) \
            .replace("<test_group>", account.entity['org_name']) \
            .replace("<threescale_superdomain>", testconfig["threescale"]["superdomain"]) \
            .replace("<account_email_domain>", account_email_domain) \
            .replace("<username>", "admin") \
            .replace("<tenant>", "3scale") \
            .replace("<service>", application['service_name']) \
            .replace("<aplan>", application['plan_name']) \
            .replace("<application>", application['name']) \
            .replace("<app_description>", application['description']) \
            .replace("\\[", "\\[") \
            .replace("\\]", "\\]")  # replaces '\\]' with '\]'

        return yaml.safe_load(yaml_string)


def headers(msg, filter_keys=None):
    """Mailhog message headers with optional filtering"""
    return {
        k: ", ".join(v)
        for k, v in msg["Content"]["Headers"].items()
        if (not filter_keys or k in filter_keys)
    }


def body(msg):
    """Mailhog message body"""
    return msg["Content"]["Body"].replace("=\r\n", "").replace("\r\n", "")


def message_match(tpl, key, text):
    """True if text matches tpl for the key"""
    for i in tpl["subject_templates"].values():
        if re.fullmatch(i[key], text):
            return True
    return False


# requires mailhog *AND* special deployment with preconfigured smtp secret
@backoff.on_exception(backoff.fibo, AssertionError, max_tries=10, jitter=None)
@pytest.mark.sandbag
def test_emails_content_after_account_creation(mailhog_client, mail_template):
    """
    Checks that the total number of matching emails is three.
    """
    tpl = mail_template  # safe few letters

    messages = [m for m in mailhog_client.all_messages()
                if message_match(tpl, "Headers", headers(m).get("X-SMTPAPI", "DO NOT MATCH"))]
    assert messages, f"Didn't find assumed X-SMTPAPI: {tpl['Headers']}"

    messages = [m for m in mailhog_client.all_messages()
                if headers(m, filter_keys=tpl["equal_templates"].keys()) == tpl["equal_templates"]]
    assert messages, f"Didn't find any email sent to expected account identified by {tpl['equal_templates']}"

    messages = [m for m in messages if message_match(tpl, "Body", body(m))]
    assert len(messages) == 3


@pytest.mark.sandbag
def test_emails_subjects_after_account_creation(mailhog_client, application):
    """Test check that all(3) messages after creating account, application and subscribing to app were sent"""
    mailhog_client.assert_message_received(
        subject=f"{application['org_name']} has subscribed to your service {application['service_name']}")
    mailhog_client.assert_message_received(
        subject=f"{application['org_name']} from {application['org_name']} signed up")
    mailhog_client.assert_message_received(
        subject=f"{application['name']} created on {application['service_name']}")
