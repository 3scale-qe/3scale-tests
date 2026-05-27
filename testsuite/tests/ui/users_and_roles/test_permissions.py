"""Tests for user permissions in 3scale"""

import pytest

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

PERMISSIONS = ["portal", "finance", "settings", "partners", "monitoring", "plans", "policy_registry"]

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
    is_page_accessible,
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
        assert is_page_accessible(page), f"A user with {user_permission} should be able to access {page_view}"
    else:
        access_denied_view = AccessDeniedView(navigator.browser.root_browser)
        assert (
            access_denied_view.is_displayed
        ), f"A user with {user_permission} should not be able to access {page_view}"
