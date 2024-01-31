"""Test of automatic email associated to accounts in UI"""

import re

import pytest

from testsuite import rawobj
from testsuite.config import settings
from testsuite.ui.views.admin.foundation import BaseAdminView
from testsuite.ui.views.admin.login import RequestAdminPasswordView, LoginView, ResetPasswordView
from testsuite.ui.views.devel import Navbar
from testsuite.ui.views.devel.login import ForgotPasswordView, LoginView as DevelLoginView
from testsuite.utils import randomize, blame


@pytest.fixture(scope="module")
def account(custom_account, request, account_password):
    """
    Account scoped for module (rather than session) because account password is updated in this module.
    """
    iname = blame(request, "id")
    account = rawobj.Account(org_name=iname, monthly_billing_enabled=False, monthly_charging_enabled=False)
    account.update(
        {
            "name": iname,
            "username": iname,
            "email": f"{iname}@example.com",
            "password": account_password,
        }
    )
    return custom_account(params=account)


def test_admin_forgotten_password(
    provider_account_user, account_password, mailhog_client, navigator, custom_admin_login
):
    """
    Test:
        - Create new provider account
        - Send reset password email
        - Assert that mail with password recovery was received
        - Reset password
        - Assert that user is unable to log in with old password
        - Assert that user is ale to log in with new password
    """
    provider_account_user.activate()
    account_name = provider_account_user.entity_name
    mail = f"{account_name}@example.com"

    navigator.open(LoginView, url=settings["threescale"]["admin"]["url"])
    reset_view = navigator.navigate(RequestAdminPasswordView)
    reset_view.reset_password(mail)

    mailhog_client.assert_message_received(subject="Password Recovery", receiver=mail, expected_count=1)

    message = mailhog_client.find_message(subject="Password Recovery", receiver=mail)

    reset_link = re.search(r"(?P<url>https?://\S+)", message["items"][0]["Content"]["Body"]).group("url")
    page = navigator.open(ResetPasswordView, url=reset_link, exact=True)
    password = randomize("password")
    page.change_password(password)

    login_view = navigator.new_page(LoginView)
    custom_admin_login(name=account_name, password=account_password, fresh=True)
    assert "Incorrect email or password. Please try again" in login_view.error_message.text

    custom_admin_login(name=account_name, password=password, fresh=True)
    assert BaseAdminView(navigator.browser).is_displayed


# pylint: disable=too-many-arguments
def test_developer_forgotten_password(
    account, account_password, provider_account, mailhog_client, navigator, custom_devel_login
):
    """
    Test:
        - Create new developer user account
        - Send reset password
        - Assert that mail with password recovery was received
    """
    account_name = account.entity_name
    mail = f"{account_name}@example.com"

    navigator.open(
        DevelLoginView, url=settings["threescale"]["devel"]["url"], access_code=provider_account["site_access_code"]
    )
    reset_view = navigator.navigate(ForgotPasswordView)
    reset_view.reset_password(mail)

    mailhog_client.assert_message_received(
        subject=f"{provider_account.entity_name} Lost password recovery. (Valid for 24 hours)",
        receiver=mail,
        expected_count=1,
    )

    message = mailhog_client.find_message(
        subject=f"{provider_account.entity_name} Lost password recovery. (Valid for 24 hours)", receiver=mail
    )

    reset_link = re.search(r"(?P<url>https?://\S+)", message["items"][0]["Content"]["Body"]).group("url")
    page = navigator.open(ResetPasswordView, url=reset_link, exact=True)
    password = randomize("password")
    page.change_password(password)

    custom_devel_login(name=account_name, password=account_password, fresh=True)
    assert not Navbar(navigator.browser).is_displayed

    custom_devel_login(name=account_name, password=password, fresh=True)
    assert Navbar(navigator.browser).is_displayed
