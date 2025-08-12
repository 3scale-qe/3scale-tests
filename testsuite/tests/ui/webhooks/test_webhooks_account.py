"""
Rewrite spec/ui_specs/webhooks/webhooks_accounts_spec.rb
"""

import xml.etree.ElementTree as Et

import pytest

from testsuite import rawobj, resilient
from testsuite.ui.views.admin.audience.account import (
    AccountEditView,
    AccountsDetailView,
    UsageRulesView,
)
from testsuite.ui.views.admin.audience.account_plan import (
    AccountPlansView,
    NewAccountPlanView,
)
from testsuite.ui.views.admin.settings.webhooks import WebhooksView
from testsuite.utils import blame

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module", autouse=True)
def setup(navigator, custom_admin_login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    """
    custom_admin_login()
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Accounts", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


@pytest.fixture(scope="module")
def account_plans(navigator, custom_admin_login):
    """
    Allow account plans
    """
    custom_admin_login()
    usage = navigator.navigate(UsageRulesView)
    usage.account_plans()


def test_account_created(requestbin, ui_account):
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


def test_account_updated(ui_account, navigator, request, requestbin, threescale):
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


# pylint: disable=too-many-locals
@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9214")
@pytest.mark.usefixtures("account_plans")
def test_account_plan_changed(account, navigator, requestbin, request, threescale):
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


def test_account_deleted(custom_account, requestbin, navigator, request):
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
