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


# Asynchronous 3scale e-mail notifications can be significantly delayed in case
# of many requests, therefore not parallel run for this.
pytestmark = [pytest.mark.disruptive]


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    "application bound to the account and service with specific description that don't break yaml parsing"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(
        rawobj.Application(blame(request, "app"), plan, "Api signup"), hooks=lifecycle_hooks,
        annotate=False)
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
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
# pylint: disable=unused-argument
@backoff.on_exception(backoff.fibo, AssertionError, 10, jitter=None)
@pytest.mark.sandbag
def test_emails_after_account_creation(mailhog_client, mail_template):
    """
    Checks that the total number of matching emails is three.
    """
    tpl = mail_template  # safe few letters

    messages = mailhog_client.messages()["items"]
    assert messages, "Mailhog inbox is empty"

    messages = [m for m in messages if message_match(tpl, "Headers", headers(m)["X-SMTPAPI"])]
    assert messages, f"Didn't find assumed X-SMTPAPI: {tpl['Headers']}"

    messages = [m for m in messages if headers(m, filter_keys=tpl["equal_templates"].keys()) == tpl["equal_templates"]]
    assert messages, f"Didn't find any email sent to expected account identified by {tpl['equal_templates']}"

    messages = [m for m in messages if message_match(tpl, "Body", body(m))]
    assert len(messages) == 3

    # Yeah! Cleanup in the test. This shouldn't be here because it won't clean
    # in case of failure. A reason to have it here is the fact that this
    # version of test doesn't contain separate function to filter tested
    # message (probably the author was lazy), also separate function scoped can
    # be dangerous due to backoff/flakiness. On the other hand it isn't that
    # "devastating" if messages are not cleaned as the mailhog receives too
    # many other emails and it is flooded anyway. However better implementation
    # with cleanup in fixture is highly desirable.
    mailhog_client.delete([m["ID"] for m in messages])
