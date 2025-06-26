"""Tests for user permissions in 3scale"""

import pytest

from testsuite.ui.views.admin.audience.billing import BillingSettingsView, BillingView
from testsuite.ui.views.admin.audience.developer_portal import (
    ActiveDocsView,
    CMSNewPageView,
    CMSNewSectionView,
    DeveloperPortalContentView,
)
from testsuite.ui.views.admin.foundation import AccessDeniedView

PERMISSION_DICT = [
    pytest.param("portal", DeveloperPortalContentView),
    pytest.param("portal", DeveloperPortalContentView),
    pytest.param("portal", CMSNewPageView),
    pytest.param("portal", CMSNewSectionView),
    pytest.param("finance", BillingView),
    pytest.param(
        "finance",
        BillingSettingsView,
        marks=[pytest.mark.xfail, pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10995")],
    ),
    pytest.param("plans", ActiveDocsView),
]


@pytest.fixture()
def all_page_objects():
    """Returns all page objects from permissions tuple filtered of views with same permission"""

    def _all_page_objects(except_permission, current_view):

        all_views = [
            view
            for perm, view in [param.values for param in PERMISSION_DICT]
            if perm != except_permission or view == current_view
        ]

        return all_views

    return _all_page_objects


# pylint: disable=too-many-arguments
@pytest.mark.parametrize("permission, page_view", PERMISSION_DICT)
def test_member_user_permissions_per_section(
    custom_admin_login,
    navigator,
    provider_member_user,
    all_page_objects,
    permission,
    page_view,
    allowed_services=False,
):
    """Tests user permissions permission per permission section"""
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
            assert AccessDeniedView(navigator.browser.root_browser).is_displayed, (
                f"{pg_obj.__name__}"
                f" should not be displayed for permissions {permission} and services {allowed_services}"
            )
