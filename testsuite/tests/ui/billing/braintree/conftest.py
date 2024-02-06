"""Conftest for Braintree gateway billing tests"""
from datetime import datetime

import pytest
import openshift_client as oc

from testsuite.billing import Braintree
from testsuite.ui.objects import CreditCard
from testsuite.ui.views.admin.audience.billing import BillingSettingsView
from testsuite.ui.views.devel.settings.braintree import BraintreeCCView
from testsuite.utils import warn_and_skip


@pytest.fixture(scope="session", autouse=True)
def require_braintree_patch(openshift):
    """Braintree requires patched deployment. No payments.yml in system configmap"""
    try:
        ocp = openshift()
        if "payments.yml" not in ocp.config_maps["system"]:
            warn_and_skip(require_braintree_patch.__doc__)
    except oc.OpenShiftPythonException:
        warn_and_skip(require_braintree_patch.__doc__)


@pytest.fixture(scope="session")
def braintree(testconfig):
    """Braintree API"""
    braintree_credentials = testconfig["braintree"]
    merchant_id = braintree_credentials["merchant_id"]
    public_key = braintree_credentials["public_key"]
    private_key = braintree_credentials["private_key"]
    return Braintree(merchant_id, public_key, private_key)


@pytest.fixture(scope="module", autouse=True)
def gateway_setup(braintree_gateway):
    """Ensures Braintree billing gateway with 3D Secure verification disabled"""
    braintree_gateway(verify_3ds=False)


@pytest.fixture(scope="module")
def braintree_gateway(custom_admin_login, navigator, testconfig, braintree):
    """
    Enables Braintree billing gateway.
    """

    def _braintree(verify_3ds: bool):
        """
        Args:
            :param verify_3ds: enable or disable 3DS verification
        """
        custom_admin_login()
        billing = navigator.navigate(BillingSettingsView)
        billing.charging(True)
        currency = braintree.merchant_currency()
        billing.charging_form.change_currency(currency)
        billing.braintree(
            testconfig["braintree"]["public_key"],
            testconfig["braintree"]["merchant_id"],
            testconfig["braintree"]["private_key"],
            verify_3ds,
        )

    return _braintree


@pytest.fixture(scope="module")
def custom_card(account, custom_devel_login, billing_address, navigator):
    """Add credit card and billing address for the user in Developer portal"""

    def _setup(cc_number, verify_3ds=False, challenge_accept=True):
        custom_devel_login(account=account)
        cc_view = navigator.navigate(BraintreeCCView)
        cc_view.add_cc_details(billing_address, CreditCard(cc_number, 123, 1, datetime.today().year + 3))
        if verify_3ds and challenge_accept:
            cc_view.challenge_form.complete()
        if verify_3ds and not challenge_accept:
            cc_view.challenge_form.cancel()
        return cc_view

    return _setup
