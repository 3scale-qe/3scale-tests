"""
Braintree gateway billing tests with 3D Secure integration for SCA compliance.
https://developer.paypal.com/braintree/docs/guides/3d-secure/testing-go-live
"""
import pytest


@pytest.mark.parametrize("cc_number,verify_3ds", [
    ("4000000000001091", True),
    ("4000000000001000", False),
], ids=[
    "with challenge", "no-challenge"
])
def test_successful(custom_card, braintree, cc_number, verify_3ds, invoice):
    """
    Tests basic billing scenario with 3DS integration for Braintree gateway:
        - Add CC details for an account
        - Complete 3DS challenge
        - Trigger billing via API
    """
    custom_card(cc_number, verify_3ds=verify_3ds)

    invoice = invoice.charge()
    braintree.assert_payment(invoice)
