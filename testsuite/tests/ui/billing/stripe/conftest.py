"""Conftest for Stripe gateway billing tests"""
import pytest

from testsuite.billing import Stripe
from testsuite.ui.objects import CreditCard
from testsuite.ui.views.admin.audience.billing import BillingSettingsView
from testsuite.ui.views.devel.settings.stripe import StripeCCView
from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def gateway_setup(custom_admin_login, navigator, testconfig):
    """Enables Stripe billing gateway"""
    custom_admin_login()
    billing = navigator.navigate(BillingSettingsView)
    billing.charging(True)
    billing.stripe(testconfig["stripe"]["secret_key"], testconfig["stripe"]["publishable_key"], "empty-webhook")


# warn_and_skip ends the test, pylint can't recognize it obviously
# pylint: disable=inconsistent-return-statements
@pytest.fixture(scope="session")
def stripe(testconfig):
    """Stripe API"""
    try:
        return Stripe(testconfig["stripe"]["api_key"])
    except KeyError:
        warn_and_skip("Stripe api_key not in config", "fail")


@pytest.fixture(scope="module")
def custom_card(account, custom_devel_login, billing_address, navigator):
    """Credit card setup"""

    def _setup(cc_number, verify_3ds=False):
        custom_devel_login(account=account)
        cc_details = CreditCard(cc_number, 123, 10, 25)
        cc_view = navigator.navigate(StripeCCView)
        cc_view.add_cc_details(billing_address, cc_details)
        if verify_3ds:
            cc_view.challenge_form.complete_auth()
        return cc_view

    return _setup
