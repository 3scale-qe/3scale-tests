"""Billing tests for Stripe payment gateway"""
import pytest


@pytest.mark.parametrize(
    "cc_number, verify_3ds",
    [
        ("4000002500003155", True),
        ("4242424242424242", False),
    ],
)
# pylint: disable=too-many-arguments
def test_3ds_challenge(custom_card, cc_number, verify_3ds, stripe, invoice, account):
    """
    Tests basic billing scenario for Stripe gateway:
        - Add CC details for an account
        - Complete 3DS challenge if it's supported
        - Trigger billing via UI
        - Trigger billing via API
    """
    custom_card(cc_number, verify_3ds)

    charged = invoice.charge()
    stripe.assert_payment(charged, account)
