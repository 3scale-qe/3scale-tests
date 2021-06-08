"""Rewrite of spec/ui_specs/dashboard_spec.rb"""
import pytest

# pylint: disable=unused-argument
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


def test_dashboard_is_loaded_correctly(login, navigator):
    """
    Test:
        - Navigates to Dashboard
        - Checks whether everything is on the dashboard that is supposed to be there
    """
    dashboard = navigator.navigate(DashboardView)

    assert dashboard.is_displayed


# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
@pytest.mark.parametrize("link, nested, view", [("create_product_button", "products", ProductNewView),
                                                ("create_backend_button", "backends", BackendNewView),
                                                ("explore_all_products", None, ProductsView),
                                                ("explore_all_backends", None, BackendsView),
                                                ("account_link", None, AccountsView),
                                                ("application_link", None, ApplicationsView),
                                                ("billing_link", None, BillingView),
                                                ("develop_portal_link", None, DeveloperPortalContentView),
                                                ("message_link", None, MessagesView)])
def test_audience_navigation_bar(login, navigator, browser, link, nested, view):
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
