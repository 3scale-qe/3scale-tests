"""
Rewrite spec/ui_specs/webhooks/webhooks_accounts_spec.rb
"""
import xml.etree.ElementTree as Et

import pytest

from testsuite.ui.views.admin import AccountsDetailView, AccountEditView, UsageRulesView, \
    AccountPlansView, NewAccountPlanView, WebhooksView
from testsuite.utils import blame


# pylint: disable=unused-argument
@pytest.fixture(scope="module", autouse=True)
def setup(navigator, login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    """
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Accounts", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def account_plans(navigator, login):
    """
    Allow account plans
    """
    usage = navigator.navigate(UsageRulesView)
    usage.account_plans()


# pylint: disable=unused-argument
def test_account_created(params, requestbin, login, create_account):
    """
    Test:
        - Create account
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """
    account = create_account(params)

    webhook = requestbin.get_webhook("created", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


# pylint: disable=too-many-arguments, unused-argument
def test_account_updated(custom_account, params, login, navigator, request, requestbin, threescale):
    """
    Test:
        - Update account
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """
    name, email, _, _ = params
    params = dict(name=name, username=name, org_name=name, email=email)
    account = custom_account(params=params)

    account_view = navigator.navigate(AccountEditView, account_id=account.entity_id)
    account_view.update(blame(request, "test_name"))
    account = threescale.accounts.read(account.entity_id)

    webhook = requestbin.get_webhook("updated", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


# pylint: disable=too-many-arguments, too-many-locals, unused-argument
def test_account_plan_changed(custom_account, params, threescale, login, navigator, requestbin, request,
                              account_plans):
    """
    Test:
        - Allow account plans
        - Change account plan
        - Get webhook response for plan_changed
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """
    name, email, _, _ = params
    params = dict(name=name, username=name, org_name=name, email=email)
    account = custom_account(params=params)

    name = blame(request, "app_plan")
    plan_view = navigator.navigate(NewAccountPlanView)
    plan_view.create(name, name)
    plan = threescale.account_plans.read_by_name(name)
    plan_view = navigator.navigate(AccountPlansView)
    plan_view.publish(plan.entity_id)
    account_view = navigator.navigate(AccountsDetailView, account_id=account.entity_id)
    account_view.change_plan(plan.entity_id)

    webhook = requestbin.get_webhook("plan_changed", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


# pylint: disable=unused-argument
def test_account_deleted(custom_account, params, requestbin, login, navigator):
    """
    Test:
        - Delete account
        - Get webhook response for deleted
        - Assert that webhook response is not None
    """
    name, email, _, _ = params
    params = dict(name=name, username=name, org_name=name, email=email)
    account = custom_account(params=params, autoclean=False)

    account_view = navigator.navigate(AccountEditView, account_id=account.entity_id)
    account_view.delete()

    webhook = requestbin.get_webhook("deleted", str(account.entity_id))
    assert webhook is not None
