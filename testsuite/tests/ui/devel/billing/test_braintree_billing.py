"""Billing tests for Braintree payment gateway"""
# pylint: disable=unused-argument
import pytest

from testsuite.ui.objects import CreditCard
from testsuite.ui.views.devel.settings.braintree import BraintreeCCView

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7762"),
    pytest.mark.sandbag,  # requires patched deployment
]


@pytest.fixture(scope="module")
def setup_card(account, custom_devel_login, billing_address, navigator):
    """Add credit card and billing address for the user in Developer portal"""
    def _setup(cc_details: CreditCard):
        custom_devel_login(account=account)
        cc_view = navigator.navigate(BraintreeCCView)
        cc_view.add_cc_details(billing_address, cc_details)

    return _setup


@pytest.fixture(scope="module", params=[pytest.param("4000000000001091", id="sca-visa")])
def sca_cards(request, braintree_gateway_sca, setup_card):
    """Braintree testing cards that support 3D Secure"""
    cc_details = CreditCard(request.param, 123, 1, 24, True)
    setup_card(cc_details)


@pytest.fixture(scope="module", params=[pytest.param("4111111111111111", id="no-sca-visa")])
def no_sca_cards(request, braintree_gateway_no_sca, setup_card):
    """"Braintree testing cards"""
    cc_details = CreditCard(request.param, 123, 1, 24, False)
    setup_card(cc_details)


@pytest.mark.parametrize("invoice_provider", ["api_invoice", "ui_invoice"])
def test_braintree_sca(request, invoice_provider, sca_cards, braintree):
    """Tests stripe billing"""
    invoice = request.getfixturevalue(invoice_provider)
    braintree.assert_payment(invoice)


@pytest.mark.parametrize("invoice_provider", ["api_invoice", "ui_invoice"])
def test_braintree_no_sca(request, invoice_provider, no_sca_cards, braintree):
    """Tests stripe billing"""
    invoice = request.getfixturevalue(invoice_provider)
    braintree.assert_payment(invoice)
