"""
Rewrite spec/ui_specs/webhooks/webhooks_users_spec.rb
"""

import xml.etree.ElementTree as Et

import pytest

from testsuite import rawobj
from testsuite.ui.views.admin import WebhooksView, AccountEditView
from testsuite.ui.views.admin.audience.account_user import AccountUserEditView
from testsuite.utils import blame


# pylint: disable=too-many-arguments, disable=unused-argument
@pytest.fixture(scope="module", autouse=True)
def setup(browser, navigator, custom_admin_login, requestbin, request, threescale):
    """
    Configure webhooks and create requestbin.
    :return: name of specific requestbin
    """
    custom_admin_login()
    webhooks = navigator.navigate(WebhooksView)
    webhooks.webhook_check("Users", requestbin.url)
    request.addfinalizer(threescale.webhooks.clear)


# pylint: disable=too-many-arguments, unused-argument
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6716")
@pytest.mark.xfail
def test_user_create(ui_account, login, navigator, requestbin, threescale):
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


# pylint: disable=too-many-arguments
def test_user_update(login, navigator, requestbin, threescale, account):
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
    user_edit.update("updated_username", "updated@anything.invalid")
    user = account.users.list()[0]
    webhook = requestbin.get_webhook("updated", str(user.entity_id))
    assert webhook is not None

    xml = Et.fromstring(webhook)
    username = xml.find(".//username").text
    email = xml.find(".//email").text
    assert username == user.entity_name
    assert email == user["email"]


# pylint: disable=too-many-arguments
def test_user_delete(login, navigator, requestbin, threescale, custom_account, request):
    """
    Test:
        - Delete account (upon deletion of account user is deleted as well)
        - Get webhook response for deleted
        - Assert that webhook response is not None
    """
    name = blame(request, "ui_account")
    params = rawobj.Account(name, None, None)
    params.update(dict(name=name, username=name, email=f"{name}@anything.invalid"))
    account = custom_account(params=params, autoclean=False)

    user = account.users.list()[0]

    account_view = navigator.navigate(AccountEditView, account=account)
    account_view.delete()
    webhook = requestbin.get_webhook("deleted", str(user.entity_id))
    assert webhook is not None
