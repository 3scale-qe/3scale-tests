"""Test for no access message in Dashboard"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.ui.views.admin.audience.support_emails import SupportEmailsView
from testsuite.ui.views.admin.foundation import DashboardView

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6321")]


# pylint: disable=unused-argument
def test_no_access_message(login, custom_admin_login, navigator, provider_account_user, browser):
    """
    Test:
        - Navigate to Support Emails view
        - Load support email
        - Login as custom provider account user
        - Assert that elements from dashboard are not displayed
        - Assert that correct message is displayed
        - Assert that href contains correct email
    """
    email = navigator.navigate(SupportEmailsView)
    email = email.support_email.read()
    provider_account_user.activate()
    custom_admin_login(provider_account_user.entity_name, "123456")
    dashboard = navigator.navigate(DashboardView)
    assert not dashboard.products.is_displayed
    assert not dashboard.backends.is_displayed

    message = browser.element(".//*[@id='apis']")
    assert message.text == "You don't have access to any API on the Provider Name account. " \
                           "Please contact admin to request access."

    href = message.find_element_by_tag_name("a").get_attribute("href")
    assert href.endswith(email)
