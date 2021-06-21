import pytest

from testsuite.tests.ui import BillingAddress, CreditCard


@pytest.fixture(scope="module")
def billing_address():
    return BillingAddress("aaa", "bbb", "Brno", "Czechia", "", "123456789", "12345")
