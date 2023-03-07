"""Braintree gateway billing tests"""
import pytest


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_no_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA disabled"""
    braintree_gateway(False)


def test_no_sca_ui_invoice(setup_card, braintree, create_ui_invoice, create_api_invoice):
    """
    Tests basic billing scenario for Braintree gateway:
        - Add CC details for an account
        - Trigger billing via UI
        - Trigger billing via API
    """
    setup_card("4111111111111111")

    invoice = create_ui_invoice()
    braintree.assert_payment(invoice)

    invoice = create_api_invoice()
    charged = invoice.charge()
    braintree.assert_payment(charged)
