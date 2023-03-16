"""Conftest for card verification enforcing 3DS verification for Braintree payment gateway """
import pytest


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_3ds_enabled(braintree_gateway):
    """Ensures Braintree billing gateway with 3D Secure verification enabled"""
    braintree_gateway(verify_3ds=True)
