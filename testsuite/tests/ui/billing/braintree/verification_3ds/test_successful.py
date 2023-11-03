"""
Braintree gateway billing tests with 3D Secure integration for SCA compliance.
https://developer.paypal.com/braintree/docs/guides/3d-secure/testing-go-live
"""
import pytest

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(
    scope="module",
    autouse=True,
    params=[
        pytest.param(("4000000000001091", True), id="3DS verification"),
        pytest.param(("4000000000001000", False), id="Without 3DS verification"),
    ],
)
def card_setup(custom_card, request):
    """Card setup"""
    custom_card(request.param[0], verify_3ds=request.param[1])


def test_successful(braintree, account, invoice):
    """
    Tests basic billing scenario with 3DS integration for Braintree gateway:
        - Add CC details for an account
        - Complete 3DS challenge
        - Trigger billing via API
    """
    transaction = braintree.ensure_single_transaction(invoice.charge, account)
    braintree.assert_payment(invoice.read(), transaction)
