"""Test of automatic mails functionality in UI"""

import re
import pytest


from testsuite.ui.views.admin.audience.account import AccountInvitationNewView
from testsuite.ui.views.devel.login import InvitationSignupView
from testsuite.utils import blame


# pylint: disable=too-many-arguments
@pytest.mark.usefixtures("login")
def test_invitation_mail(account, navigator, mailhog_client, provider_account, request, custom_devel_login, browser):
    """
    Test:
        - Send invitation to new user
        - Assert that invitation were sent via mail
        - Signup with email signup link
        - Login with new signed-up user
        - Assert that login was successful
    """
    email = f"{blame(request, 'mail')}@anything.invalid"
    username = blame(request, "user")
    password = blame(request, "passwd")

    invitation = navigator.navigate(AccountInvitationNewView, account=account)
    invitation.invite_user(email)

    # assert inside mailhog method
    mail = mailhog_client.assert_message_received(
        subject=f"Invitation to join {account.entity_name}", receiver=email, expected_count=1
    )
    # extract invitation URL from invitation mail
    url = re.search(r"(?P<url>https?://[^\s]+)", mail["items"][0]["Content"]["Body"]).group("url")
    sign_page = navigator.open(
        InvitationSignupView,
        url=url,
        exact=True,
        access_code=provider_account["site_access_code"],
        wait_displayed=False,
    )

    assert sign_page.is_displayed
    assert sign_page.email.value == email

    sign_page.sign_up(username=username, passwd=password)

    custom_devel_login(name=username, password=password)

    assert "SIGNED IN SUCCESSFULLY" in browser.element('//*[@id="flash-messages"]/div/div').text
