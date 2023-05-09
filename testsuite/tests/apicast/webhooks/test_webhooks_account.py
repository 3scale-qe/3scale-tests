"""
Based on spec/ui_specs/webhooks/webhooks_accounts_spec.rb (ruby test is via UI)
"""

import xml.etree.ElementTree as Et

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.utils import blame

# webhook tests seem disruptive to requestbin as they reset it with no mercy
pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.8.3')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5207"),
    pytest.mark.disruptive,
]


@pytest.fixture(scope="module", autouse=True)
def setup(requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    :return: name of specific requestbin
    """
    threescale.webhooks.setup("Accounts", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


@pytest.fixture(scope="function")
def params(request):
    """
    :return: params for custom account
    """
    name = blame(request, "id")

    return {"name": name, "username": name, "org_name": name, "email": f"{name}@anything.invalid"}


def test_account_created(custom_account, params, requestbin):
    """
    Test:
        - Create account
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """

    account = custom_account(params=params)

    webhook = requestbin.get_webhook("created", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


def test_account_updated(account, request, requestbin):
    """
    Test:
        - Update account
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """

    account.update(params={"org_name": blame(request, "test_name")})

    webhook = requestbin.get_webhook("updated", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


def test_account_plan_changed(threescale, account, request, requestbin):
    """
    Test:
        - Change account plan
        - Get webhook response for plan_changed
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """

    plan = threescale.account_plans.create(params={"name": blame(request, "acc_plan")})
    threescale.accounts.set_plan(account.entity_id, plan.entity_id)
    webhook = requestbin.get_webhook("plan_changed", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


def test_account_deleted(custom_account, params, requestbin):
    """
    Test:
        - Delete account
        - Get webhook response for deleted
        - Assert that webhook response is not None
    """

    account = custom_account(params=params, autoclean=False)
    account.delete()

    webhook = requestbin.get_webhook("deleted", str(account.entity_id))
    assert webhook is not None
