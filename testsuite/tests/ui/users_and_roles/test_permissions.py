"""Tests for user permissions in 3scale"""

import pytest

from testsuite.ui.views.admin.audience.billing import BillingView, BillingSettingsView
from testsuite.ui.views.admin.audience.developer_portal import (
    DeveloperPortalContentView,
    CMSNewPageView,
    CMSNewSectionView,
    ActiveDocsView,
)
from testsuite.ui.views.admin.backend import BackendsView
from testsuite.ui.views.admin.foundation import DashboardView, AccessDeniedView
from testsuite.ui.views.admin.product import ProductsView
from testsuite.ui.views.admin.product.integration.settings import ProductSettingsView


PERMISSION_DICT = [
    ("portal", DeveloperPortalContentView, None, None),
    ("portal", CMSNewPageView, None, None),
    ("portal", CMSNewSectionView, None, None),
    ("finance", BillingView, None, None),
    (
        "finance",
        BillingSettingsView,
        pytest.mark.xfail,
        pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3368"),
    ),
    ("plans", ActiveDocsView, None, None),
]


def get_views_by_permission(permission_name):
    """Returns a list of views that has the given permission by permission name"""
    return [view for perm, view, _, _ in PERMISSION_DICT if perm == permission_name]


@pytest.fixture()
def all_page_objects():
    def _all_page_objects(except_permission, current_view):
        """Returns all page objects from permissions tuple filtered of views with same permission"""

        all_views = [
            view
            for perm, view, xfail_mark, issue_mark in PERMISSION_DICT
            if perm != except_permission or view == current_view
        ]

        return all_views

    return _all_page_objects


@pytest.mark.parametrize("permission, page_view, xfail_mark, issue_mark", PERMISSION_DICT)
def test_member_user_permissions_per_section(
    custom_admin_login,
    navigator,
    provider_member_user,
    all_page_objects,
    permission,
    page_view,
    xfail_mark,
    issue_mark,
    allowed_services=None,
):
    member_user = provider_member_user(allowed_sections=permission, allowed_services=allowed_services)
    custom_admin_login(member_user.entity_name, "123456")

    page_objects = all_page_objects(permission, page_view)

    for pg_obj in page_objects:
        # Dynamically import the view class
        view_module = __import__(pg_obj.__module__, fromlist=[pg_obj.__name__])
        page_class = getattr(view_module, pg_obj.__name__)
        page = navigator.open(page_class, wait_displayed=False)

        if pg_obj == page_view:
            assert (
                page.is_displayed
            ), f"{pg_obj.__name__} should be displayed for permissions {permission} and services {allowed_services}"
        else:
            assert AccessDeniedView(
                navigator.browser.root_browser
            ).is_displayed, f"{pg_obj.__name__} should not be displayed for permissions {permission} and services {allowed_services}"
