"""
Rewrite spec/ui_specs/webhooks/webhooks_accounts_spec.rb
"""
import xml.etree.ElementTree as Et

import pytest

from testsuite import rawobj, resilient
from testsuite.ui.views.admin.audience.account import UsageRulesView, AccountEditView, AccountsDetailView
from testsuite.ui.views.admin.audience.account_plan import NewAccountPlanView, AccountPlansView
from testsuite.ui.views.admin.settings.webhooks import WebhooksView
from testsuite.utils import blame


# pylint: disable=unused-argument
@pytest.fixture(scope="module", autouse=True)
def setup(navigator, custom_admin_login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    """
    custom_admin_login()
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Accounts", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def account_plans(navigator, custom_admin_login):
    """
    Allow account plans
    """
    custom_admin_login()
    usage = navigator.navigate(UsageRulesView)
    usage.account_plans()


# pylint: disable=unused-argument
def test_account_created(requestbin, login, ui_account):
    """
    Test:
        - Create account
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """
    webhook = requestbin.get_webhook("created", str(ui_account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == ui_account.entity_name


# pylint: disable=too-many-arguments, unused-argument
def test_account_updated(ui_account, login, navigator, request, requestbin, threescale):
    """
    Test:
        - Update account
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """
    account_view = navigator.navigate(AccountEditView, account=ui_account)
    account_view.update(blame(request, "test_name"))
    ui_account = threescale.accounts.read(ui_account.entity_id)

    webhook = requestbin.get_webhook("updated", str(ui_account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == ui_account.entity_name


# pylint: disable=too-many-arguments, too-many-locals, unused-argument
def test_account_plan_changed(account, threescale, login, navigator, requestbin, request, account_plans):
    """
    Test:
        - Allow account plans
        - Change account plan
        - Get webhook response for plan_changed
        - Assert that webhook response is not None
        - Assert that response xml body contains right account name
    """
    name = blame(request, "app_plan")
    plan_view = navigator.navigate(NewAccountPlanView)
    plan_view.create(name, name)
    plan = resilient.resource_read_by_name(threescale.account_plans, name)
    plan_view = navigator.navigate(AccountPlansView)
    plan_view.publish(plan.entity_name)
    account_view = navigator.navigate(AccountsDetailView, account=account)
    account_view.change_plan(plan.entity_id)

    webhook = requestbin.get_webhook("plan_changed", str(account.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    name = xml.find(".//org_name").text
    assert name == account.entity_name


# pylint: disable=unused-argument
def test_account_deleted(custom_account, requestbin, login, navigator, request):
    """
    Test:
        - Delete account
        - Get webhook response for deleted
        - Assert that webhook response is not None
    """
    name = blame(request, "ui_account")
    params = rawobj.Account(name, None, None)
    params.update({"name": name, "username": name, "email": f"{name}@anything.invalid"})
    account = custom_account(params=params, autoclean=False)

    account_view = navigator.navigate(AccountEditView, account=account)
    account_view.delete()

    webhook = requestbin.get_webhook("deleted", str(account.entity_id))
    assert webhook is not None
