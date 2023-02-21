"""Conftest for Braintree gateway billing tests"""
import pytest

from testsuite.ui.objects import CreditCard
from testsuite.ui.views.admin.audience.billing import BillingSettingsView
from testsuite.ui.views.devel.settings.braintree import BraintreeCCView


pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7762"),
    pytest.mark.sandbag,  # requires patched deployment
]


@pytest.fixture(scope="module")
def braintree_gateway(custom_admin_login, navigator, testconfig, braintree):
    """
    Enables Braintree billing gateway.
    """
    def _braintree(sca):
        """
        Args:
            :param sca: enable or disable SCA for the gateway; possible values True or False
        """
        custom_admin_login()
        billing = navigator.navigate(BillingSettingsView)
        billing.charging(True)
        currency = braintree.merchant_currency()
        billing.charging_form.change_currency(currency)
        billing.braintree(testconfig["braintree"]["public_key"],
                          testconfig["braintree"]["merchant_id"],
                          testconfig["braintree"]["private_key"],
                          sca)

    return _braintree


@pytest.fixture(scope="module")
def setup_card(account, custom_devel_login, billing_address, navigator):
    """Add credit card and billing address for the user in Developer portal"""
    def _setup(cc_number, verify_3ds=False):
        custom_devel_login(account=account)
        cc_view = navigator.navigate(BraintreeCCView)
        cc_view.add_cc_details(billing_address, CreditCard(cc_number, 123, 1, 24))
        if verify_3ds:
            cc_view.challenge_form.complete()
        return cc_view

    return _setup
