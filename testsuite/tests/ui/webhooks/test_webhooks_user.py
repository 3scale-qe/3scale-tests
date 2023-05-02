"""
Rewrite spec/ui_specs/webhooks/webhooks_users_spec.rb
"""

import xml.etree.ElementTree as Et

import pytest

from testsuite import rawobj
from testsuite.ui.views.admin.audience.account import AccountEditView
from testsuite.ui.views.admin.audience.account_user import AccountUserEditView
from testsuite.ui.views.admin.settings.webhooks import WebhooksView
from testsuite.utils import blame

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module", autouse=True)
def setup(navigator, custom_admin_login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    :return: name of specific requestbin
    """
    custom_admin_login()
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Users", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6716")
@pytest.mark.xfail
def test_user_create(ui_account, requestbin):
    """
    Test:
        - Create account (upon creation of account user is created as well)
        - Get webhook response for created
        - Assert that webhook response is not None
        - Assert that response xml body contains right username
        - Assert that response xml body contains right email
    """
    user = ui_account.users.list()[0]
    webhook = requestbin.get_webhook("created", str(user.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    username = xml.find(".//username").text
    email = xml.find(".//email").text
    assert username == user.entity_name
    assert email == user["email"]


def test_user_update(navigator, requestbin, account, request):
    """
     Test:
        - Update user
        - Get webhook response for updated
        - Assert that webhook response is not None
        - Assert that response xml body contains right username
        - Assert that response xml body contains right email
    """
    user = account.users.list()[0]
    user_edit = navigator.navigate(AccountUserEditView, account=account, user=user)
    updated_name = blame(request, "updated")
    user_edit.update(updated_name, updated_name + "@example.com")

    user = account.users.list()[0]
    webhook = requestbin.get_webhook("updated", str(user.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    username = xml.find(".//username").text
    email = xml.find(".//email").text
    assert username == user.entity_name
    assert email == user["email"]


def test_user_delete(navigator, requestbin, custom_account, request):
    """
    Test:
        - Delete account (upon deletion of account user is deleted as well)
        - Get webhook response for deleted
        - Assert that webhook response is not None
    """
    name = blame(request, "ui_account")
    params = rawobj.Account(name, None, None)
    params.update({"name": name, "username": name, "email": f"{name}@anything.invalid"})
    account = custom_account(params=params, autoclean=False)

    user = account.users.list()[0]

    account_view = navigator.navigate(AccountEditView, account=account)
    account_view.delete()
    webhook = requestbin.get_webhook("deleted", str(user.entity_id))
    assert webhook is not None
