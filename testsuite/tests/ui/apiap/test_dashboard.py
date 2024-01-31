"""Rewrite of spec/ui_specs/dashboard_spec.rb"""

import pytest

from testsuite import TESTED_VERSION
from testsuite.config import settings
from testsuite.ui.views.admin.audience.account import AccountsView
from testsuite.ui.views.admin.audience.application import ApplicationsView
from testsuite.ui.views.admin.audience.billing import BillingView
from testsuite.ui.views.admin.audience.developer_portal import DeveloperPortalContentView
from testsuite.ui.views.admin.audience.messages import MessagesView
from testsuite.ui.views.admin.backend import BackendsView
from testsuite.ui.views.admin.backend.backend import BackendNewView
from testsuite.ui.views.admin.foundation import DashboardView
from testsuite.ui.views.admin.product import ProductsView
from testsuite.ui.views.admin.product.product import ProductNewView

pytestmark = pytest.mark.usefixtures("login")


def test_dashboard_is_loaded_correctly(navigator):
    """
    Test:
        - Navigates to Dashboard
        - Checks whether everything is on the dashboard that is supposed to be there
    """
    dashboard = navigator.navigate(DashboardView)

    assert dashboard.is_displayed


@pytest.mark.parametrize(
    "link, nested, view",
    [
        ("create_product_button", "products", ProductNewView),
        ("create_backend_button", "backends", BackendNewView),
        ("explore_all_products", None, ProductsView),
        ("explore_all_backends", None, BackendsView),
        ("account_link", None, AccountsView),
        ("application_link", None, ApplicationsView),
        ("billing_link", None, BillingView),
        ("develop_portal_link", None, DeveloperPortalContentView),
        ("message_link", None, MessagesView),
    ],
)
def test_audience_navigation_bar(navigator, browser, link, nested, view):
    """
    Test:
        - Navigates to Dashboard
        - tests whether the buttons "account, application, billings ..." navigates to correct endpoints
    """
    dashboard = navigator.navigate(DashboardView)
    if nested:
        getattr(getattr(dashboard, nested, None), link, None).click()
    else:
        getattr(dashboard, link, None).click()

    assert view(browser).is_displayed


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6209")
@pytest.mark.skipif_devrelease
def test_3scale_version_in_ui(navigator):
    """
    Test:
        - Navigate to Dashboard
        - Assert that 3scale version is displayed and is correct
    """
    dashboard = navigator.open(DashboardView)
    assert dashboard.threescale_version.is_displayed
    if settings["threescale"]["deployment_type"] == "rhoam":
        assert dashboard.threescale_version.text == "Version RHOAM -"
    else:
        assert dashboard.threescale_version.text == f"Version {TESTED_VERSION.release[0]}.{TESTED_VERSION.release[1]} -"
