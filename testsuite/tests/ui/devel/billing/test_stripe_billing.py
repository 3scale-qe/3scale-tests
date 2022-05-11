"""Billing tests for Stripe payment gateway"""
# pylint: disable=unused-argument
import pytest

from testsuite.ui.objects import CreditCard
from testsuite.ui.views.devel.settings.stripe import StripeCCView


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module", params=[
    pytest.param(("4000002500003155", True), id="sca-visa"),
    pytest.param(("4242424242424242", False)),
])
def stripe_card(request, account, stripe_gateway, custom_devel_login, billing_address, navigator):
    """Credit card details"""
    custom_devel_login(account=account)
    cc_details = CreditCard(request.param[0], 123, 10, 25, request.param[1])
    cc_view = navigator.navigate(StripeCCView)
    cc_view.add_cc_details(billing_address, cc_details)


@pytest.mark.parametrize("invoice_provider", ["api_invoice", "ui_invoice"])
def test_stripe(request, account, threescale, stripe_card, invoice_provider, stripe):
    """Tests stripe billing"""
    old = threescale.invoices.list_by_account(account)
    request.getfixturevalue(invoice_provider)
    acc_invoices = threescale.invoices.list_by_account(account)
    assert len(acc_invoices) - len(old) == 1
    stripe.assert_payment(acc_invoices[0])
