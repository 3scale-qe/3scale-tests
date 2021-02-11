"""UI webhook conftest"""

import pytest

from testsuite.ui.views.admin import NewAccountView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def create_account(navigator, threescale, request, testconfig):
    """
    Create a custom account
    """

    def _create_account(params, autoclean=True):
        name, email, password, org_name = params
        account = navigator.navigate(NewAccountView)
        account.create(name, email, password, org_name)
        account = threescale.accounts.read_by_name(name)

        if autoclean and not testconfig["skip_cleanup"]:
            request.addfinalizer(account.delete)
        return account

    return _create_account


@pytest.fixture(scope="function")
def params(request):
    """
    :return: params for custom account
    """
    name = blame(request, "id")
    return name, f"{name}@anything.invalid", name, name
