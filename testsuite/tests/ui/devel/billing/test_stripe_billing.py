"""Billing tests for Stripe payment gateway"""
import pytest

from testsuite.ui.objects import CreditCard
from testsuite.ui.views.admin.audience.billing import BillingSettingsView
from testsuite.ui.views.devel.settings.stripe import StripeCCView


@pytest.fixture(scope="module", autouse=True)
def stripe_gateway(custom_admin_login, navigator, testconfig):
    """Enables Stripe billing gateway"""
    custom_admin_login()
    billing = navigator.navigate(BillingSettingsView)
    billing.charging(True)
    billing.stripe(testconfig["stripe"]["secret_key"],
                   testconfig["stripe"]["publishable_key"],
                   "empty-webhook")


@pytest.fixture(scope="module")
def setup_card(account, custom_devel_login, billing_address, navigator):
    """Credit card setup"""
    def _setup(cc_number, sca):
        custom_devel_login(account=account)
        cc_details = CreditCard(cc_number, 123, 10, 25, sca)
        cc_view = navigator.navigate(StripeCCView)
        cc_view.add_cc_details(billing_address, cc_details)

    return _setup


@pytest.mark.parametrize("cc_number, verify_3ds", [
    ("4000002500003155", True),
    ("4242424242424242", False),
])
# pylint: disable=too-many-arguments
def test_stripe(setup_card, cc_number, verify_3ds, stripe, create_ui_invoice, create_api_invoice):
    """
    Tests basic billing scenario for Stripe gateway:
        - Add CC details for an account
        - Complete 3DS challenge if it's supported
        - Trigger billing via UI
        - Trigger billing via API
    """
    setup_card(cc_number, verify_3ds)

    invoice = create_ui_invoice()
    stripe.assert_payment(invoice)

    invoice = create_api_invoice()
    stripe.assert_payment(invoice)
