"""Billing tests for Stripe payment gateway"""

import pytest


@pytest.fixture(
    scope="module",
    autouse=True,
    params=[
        pytest.param(("4000002500003155", True), id="EU card, 3ds verification required"),
        pytest.param(("4242424242424242", False), id="US card, no verification"),
        pytest.param(("4000002030000002", False), id="EU card, no verification"),
    ],
)
def card_setup(request, custom_card):
    """Card setup"""
    custom_card(request.param[0], verify_3ds=request.param[1])


def test_3ds_challenge(stripe, invoice, account):
    """
    Tests basic billing scenario for Stripe gateway:
        - Add CC details for an account
        - Complete 3DS challenge if it's supported
        - Trigger billing via UI
        - Trigger billing via API
    """
    charged = invoice.charge()
    stripe.assert_payment(charged, account)
