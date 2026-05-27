"""Tests for user permissions in 3scale"""

import pytest
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from widgetastic.widget import GenericLocatorWidget

from testsuite.ui.views.admin.audience.account import AccountsView
from testsuite.ui.views.admin.audience.billing import (
    BillingSettingsView,
    BillingView,
)
from testsuite.ui.views.admin.audience.developer_portal import (
    ActiveDocsView,
    CMSNewPageView,
    CMSNewSectionView,
    DeveloperPortalContentView,
)
from testsuite.ui.views.admin.backend.analytics import BackendTrafficView
from testsuite.ui.views.admin.foundation import AccessDeniedView

VIEWS = [
    ("portal", DeveloperPortalContentView),
    ("portal", CMSNewPageView),
    ("portal", CMSNewSectionView),
    ("finance", BillingView),
    ("finance", BillingSettingsView),
    ("plans", ActiveDocsView),
    ("monitoring", BackendTrafficView),
    ("partners", AccountsView),
]

PERMISSIONS = list({permission for permission, _ in VIEWS})


def _is_page_accessible(page):
    """Check if a page is accessible by verifying URL path and masthead presence."""
    if page.path not in page.browser.url:
        return False

    try:
        masthead = GenericLocatorWidget(
            page, locator="//header[contains(@class, 'pf-c-masthead') and contains(@class, 'pf-m-display-inline')]"
        )
        if not masthead.is_displayed:
            return False
    except (NoSuchElementException, WebDriverException):
        return False

    return True


# pylint: disable=too-many-arguments
@pytest.mark.parametrize("user_permission", PERMISSIONS)
@pytest.mark.parametrize("required_permission, page_view", VIEWS)
def test_member_user_permissions_per_section(
    account_password,
    custom_admin_login,
    navigator,
    provider_member_user,
    backend_default,
    user_permission,
    required_permission,
    page_view,
):
    """
    Tests user permissions permission per permission section
        - Creates a member user with a specific permission
        - Logs in as that member user
        - Attempts to access a specific UI page
        - If users permission matches page's required permission -> allowed
        - Else, access denied
    """
    member_user = provider_member_user(allowed_sections=[user_permission], allowed_services=None)
    custom_admin_login(member_user.entity_name, account_password)

    if page_view == BackendTrafficView:
        page = navigator.open(page_view, backend=backend_default, wait_displayed=False)
    else:
        page = navigator.open(page_view, wait_displayed=False)

    if user_permission == required_permission:
        assert _is_page_accessible(page), f"A user with {user_permission} should be able to access {page_view}"
    else:
        access_denied_view = AccessDeniedView(navigator.browser.root_browser)
        assert (
            access_denied_view.is_displayed
        ), f"A user with {user_permission} should not be able to access {page_view}"
