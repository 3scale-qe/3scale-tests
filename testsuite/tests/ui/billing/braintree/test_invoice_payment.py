"""Braintree gateway billing tests"""
import pytest


pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7762"),
]


@pytest.fixture(scope="module", autouse=True)
def braintree_gateway_3ds_disabled(braintree_gateway):
    """Ensures Braintree billing gateway with 3D Secure verification disabled"""
    braintree_gateway(verify_3ds=False)


@pytest.fixture(scope="module", autouse=True)
def card_setup(custom_card):
    """Card setup"""
    custom_card("4111111111111111")


def test_no_sca_ui_invoice(braintree, ui_invoice):
    """Tests basic billing scenario for Braintree gateway where billing is triggered via UI"""
    invoice_view = ui_invoice()
    invoice_view.charge()
    braintree.assert_payment(invoice_view.invoice.read())
    assert invoice_view.state_field.text == "Paid"


def test_api(braintree, invoice):
    """Tests basic billing scenario for Braintree gateway where billing is triggered via UI"""
    charged = invoice.charge()
    braintree.assert_payment(charged)
