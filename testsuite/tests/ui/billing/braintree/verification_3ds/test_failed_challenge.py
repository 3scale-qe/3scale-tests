"""
Successful Challenge Authentication:
Cardholder enrolled, authentication successful, and signature verification successful.
"""

import pytest
from threescale_api.errors import ApiClientError

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(("4000000000001109", True), id="Challenge accepted"),
        pytest.param(("4000000000001091", False), id="Challenge canceled"),
    ],
)
def card_setup(custom_card, request):
    """Card setup"""
    view = custom_card(request.param[0], verify_3ds=True, challenge_accept=request.param[1])
    return view


def test_cancel_challenge(braintree, card_setup, account, invoice):
    """
    Test scenario:
        - Add CC details for an account
        - Cancel 3DS challenge
        - Verify that CC was not added
    """
    assert card_setup.alert() == "An error occurred, please review your CC details or try later."

    with pytest.raises(ApiClientError) as exc_info:
        transaction = braintree.ensure_single_transaction(invoice.charge, account)
        braintree.assert_declined_payment(invoice.read(), transaction)

    assert exc_info.type is ApiClientError
    assert "422 Unprocessable Entity" in exc_info.value.args[0]
    assert "Failed to charge the credit card" in exc_info.value.args[0]
