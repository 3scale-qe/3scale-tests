"""Braintree gateway billing tests"""
import pytest


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_no_sca(braintree_gateway):
    """Ensures Braintree billing gateway with SCA disabled"""
    braintree_gateway(verify_3ds=False)


@pytest.fixture(scope="module", autouse=True)
def setup_card(setup_card):
    """Card setup"""
    setup_card("4111111111111111")


def test_no_sca_ui_invoice(braintree, create_ui_invoice):
    """Tests basic billing scenario for Braintree gateway where billing is triggered via UI"""
    invoice = create_ui_invoice()
    braintree.assert_payment(invoice)


def test_api(braintree, create_api_invoice):
    """Tests basic billing scenario for Braintree gateway where billing is triggered via UI"""
    invoice = create_api_invoice()
    charged = invoice.charge()
    braintree.assert_payment(charged)
