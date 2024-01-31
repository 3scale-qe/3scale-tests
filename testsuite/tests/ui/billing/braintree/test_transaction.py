"""
Tests for transaction
https://developer.paypal.com/braintree/docs/reference/general/testing/python
https://developer.paypal.com/braintree/docs/reference/general/statuses#transaction
"""

import pytest
from threescale_api.errors import ApiClientError

from testsuite.ui.views.admin.audience.account import InvoiceDetailView

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module", autouse=True)
def card_setup(custom_card):
    """Card setup"""
    custom_card("4111111111111111")


def test_successful_payment(braintree, custom_invoice, navigator, account):
    """Tests successful transaction with cost of 1000  Approved"""
    invoice = custom_invoice(1000)
    transaction = braintree.ensure_single_transaction(invoice.charge, account)
    invoice = invoice.read()
    braintree.assert_payment(invoice, transaction)

    view = navigator.open(InvoiceDetailView, account=account, invoice=invoice)
    view.assert_transaction(invoice)


def test_declined_payment(braintree, custom_invoice, navigator, account):
    """Tests declined transaction with cost of 2017 - Cardholder Stopped Billing"""
    invoice = custom_invoice(2017)
    with pytest.raises(ApiClientError) as exc_info:
        transaction = braintree.ensure_single_transaction(invoice.charge, account)
        braintree.assert_declined_payment(invoice, transaction)

    invoice = invoice.read()
    assert exc_info.type is ApiClientError
    assert "422 Unprocessable Entity" in exc_info.value.args[0]
    assert "Failed to charge the credit card" in exc_info.value.args[0]

    view = navigator.open(InvoiceDetailView, account=account, invoice=invoice)
    view.assert_transaction(invoice)
