"""
Braintree gateway billing tests with 3D Secure integration for SCA compliance.
https://developer.paypal.com/braintree/docs/guides/3d-secure/testing-go-live
"""
import pytest


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA enabled"""
    braintree_gateway(True)


def test_sca_ui_invoice(setup_card, braintree, create_ui_invoice, create_api_invoice):
    """
    Tests basic billing scenario with 3DS integration for Braintree gateway:
        - Add CC details for an account
        - Complete 3DS challenge
        - Trigger billing via UI
        - Trigger billing via API
    """
    setup_card("4000000000001091", True)

    invoice = create_ui_invoice()
    braintree.assert_payment(invoice)

    invoice = create_api_invoice()
    braintree.assert_payment(invoice)
