"""
Braintree gateway billing tests with 3D Secure integration for SCA compliance.
https://developer.paypal.com/braintree/docs/guides/3d-secure/testing-go-live
"""
import pytest
from threescale_api.errors import ApiClientError


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA enabled"""
    braintree_gateway(verify_3ds=True)


def test_successful_with_challenge(setup_card, braintree, create_ui_invoice, create_api_invoice):
    """
    Tests basic billing scenario with 3DS integration for Braintree gateway:
        - Add CC details for an account
        - Complete 3DS challenge
        - Trigger billing via UI
        - Trigger billing via API
    """
    setup_card("4000000000001091", verify_3ds=True)

    invoice = create_ui_invoice()
    braintree.assert_payment(invoice)

    invoice = create_api_invoice()
    invoice = invoice.charge()
    braintree.assert_payment(invoice)


def test_successful_without_challenge(setup_card, braintree, create_api_invoice):
    """
    Test scenario: Cardholder enrolled, authentication successful, and signature verification successful:
        - Add CC details for an account
        - Trigger billing via API
    """
    setup_card("4000000000001000")

    invoice = create_api_invoice()
    invoice = invoice.charge()
    braintree.assert_payment(invoice)


def test_unsuccessful_with_challenge(account, setup_card, create_api_invoice):
    """
    Test scenario: Cardholder enrolled, authentication unsuccessful.
    Merchants should prompt customers for another form of payment:
        - Clears all CC data for an account
        - Add CC details for an account
        - Verify that CC was not added
    """
    account.credit_card_delete()
    cc_view = setup_card("4000000000001109", verify_3ds=True)
    assert cc_view.alert() == "An error occurred, please review your CC details or try later."

    invoice = create_api_invoice()
    with pytest.raises(ApiClientError) as exc_info:
        invoice.charge()

    assert exc_info.type is ApiClientError
    assert "422 Unprocessable Entity" in exc_info.value.args[0]
    assert "Failed to charge the credit card" in exc_info.value.args[0]


def test_cancel_challenge(account, setup_card, create_api_invoice):
    """
    Test scenario: Cardholder enrolled, authentication successful, and signature verification successful:
        - Clears all CC data for an account
        - Add CC details for an account
        - Cancel 3DS challenge
        - Verify that CC was not added
    """
    account.credit_card_delete()
    cc_view = setup_card("4000000000001091")
    cc_view.challenge_form.cancel()
    assert cc_view.alert() == "An error occurred, please review your CC details or try later."

    invoice = create_api_invoice()
    with pytest.raises(ApiClientError) as exc_info:
        invoice.charge()

    assert exc_info.type is ApiClientError
    assert "422 Unprocessable Entity" in exc_info.value.args[0]
    assert "Failed to charge the credit card" in exc_info.value.args[0]
