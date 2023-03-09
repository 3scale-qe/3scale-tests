"""
Braintree gateway billing tests with 3D Secure integration for SCA compliance.
https://developer.paypal.com/braintree/docs/guides/3d-secure/testing-go-live
"""
import pytest


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA enabled"""
    braintree_gateway(verify_3ds=True)


@pytest.mark.parametrize("cc_number,verify_3ds", [
    ("4000000000001091", True),
    ("4000000000001000", False),
], ids=[
    "with challenge", "no-challenge"
])
def test_successful(setup_card, braintree, cc_number, verify_3ds, create_api_invoice):
    """
    Tests basic billing scenario with 3DS integration for Braintree gateway:
        - Add CC details for an account
        - Complete 3DS challenge
        - Trigger billing via API
    """
    setup_card(cc_number, verify_3ds=verify_3ds)

    invoice = create_api_invoice()
    invoice = invoice.charge()
    braintree.assert_payment(invoice)
