"""Billing tests for Stripe payment gateway"""
import pytest


@pytest.mark.parametrize("cc_number, verify_3ds", [
    ("4000002500003155", True),
    ("4242424242424242", False),
])
def test_3ds_challenge(setup_card, cc_number, verify_3ds, stripe, create_api_invoice):
    """
    Tests basic billing scenario for Stripe gateway:
        - Add CC details for an account
        - Complete 3DS challenge if it's supported
        - Trigger billing via UI
        - Trigger billing via API
    """
    setup_card(cc_number, verify_3ds)

    invoice = create_api_invoice()
    charged = invoice.charge()
    stripe.assert_payment(charged)
