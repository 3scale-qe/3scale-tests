"""Test that system is not sending mail notification to suspended users"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.ui.views.admin.settings.user import UserDetailView
from testsuite.utils import blame


@pytest.fixture()
def ui_account(request, custom_ui_account):
    """Creates a custom account via UI"""

    def _ui_account():
        username = blame(request, "username")
        org_name = blame(request, "org_name")
        email = f"{username}@anything.invalid"
        return custom_ui_account(username, email, "123456", org_name)

    return _ui_account


@pytest.fixture()
def provider_account_user(navigator, provider_account_user):
    """
    Activate a provider account and give it an admin role
    """
    provider_account_user.activate()
    user_view = navigator.navigate(UserDetailView, user=provider_account_user)
    user_view.set_admin_role()
    user_view.update_btn.click()
    return provider_account_user


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8903")
@pytest.mark.usefixtures("login")
@pytest.mark.skipif("TESTED_VERSION < Version('2.14-dev')")
def test_mail_to_suspended_user(provider_account_user, ui_account, mailhog_client):
    """
    Test:
        - Creates an account via UI
        - Assert that user received email about account creation
        - Suspend account
        - Creates another account via UI
        - Assert that suspended user doesn't receive an email about account creation
    """
    pre_suspend_acc = ui_account()
    mailhog_client.assert_message_received(
        subject=f"{pre_suspend_acc.users.list()[0]['username']} from {pre_suspend_acc['org_name']} signed up",
        receiver=provider_account_user["email"],
        expected_count=1,
    )
    provider_account_user.suspend()
    post_suspend_acc = ui_account()
    mailhog_client.assert_message_received(
        subject=f"{post_suspend_acc.users.list()[0]['username']} from {post_suspend_acc['org_name']} signed up",
        receiver=provider_account_user["email"],
        expected_count=0,
    )
