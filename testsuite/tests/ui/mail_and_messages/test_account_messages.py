"""Test of automatic email associated to accounts in UI"""
from testsuite.config import settings
from testsuite.ui.views.admin.login import ResetAdminPasswordView, LoginView
from testsuite.ui.views.devel.login import ForgotPasswordView, LoginView as DevelLoginView


def test_admin_forgotten_password(provider_account_user, mailhog_client, navigator):
    """
    Test:
        - Create new provider account
        - Send reset password
        - Assert that mail with password recovery was received
    """
    mail = f"{provider_account_user.entity_name}@example.com"

    navigator.open(LoginView, url=settings["threescale"]["admin"]["url"])
    reset_view = navigator.navigate(ResetAdminPasswordView)
    reset_view.reset_password(mail)

    mailhog_client.assert_message_received(subject="Password Recovery", receiver=mail, expected_count=1)


def test_developer_forgotten_password(account, provider_account, mailhog_client, navigator):
    """
    Test:
        - Create new developer user account
        - Send reset password
        - Assert that mail with password recovery was received
    """
    mail = f"{account.entity_name}@example.com"

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
