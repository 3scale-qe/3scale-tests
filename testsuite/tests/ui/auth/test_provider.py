"""
Tests for admin portal SSO integrations
Rewrite of spec/ui_specs/oauth/provider_rhsso_spec.rb and provider_auth0_spec.rb
"""
import pytest

from testsuite.ui.views.admin.foundation import BaseAdminView


@pytest.mark.parametrize(
    "login",
    [
        "auth0_login",
        "auth0_bounce_login",
        "rhsso_login",
        pytest.param(
            "rhsso_bounce_login", marks=[pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-1292")]
        ),
    ],
)
def test_provider(navigator, login, request):
    """
    Test:
        - login to 3scale via Auth0/RHSSO
        - assert that you are logged in
    """
    request.getfixturevalue(login)
    admin_view = navigator.navigate(BaseAdminView)
    assert admin_view.wait_displayed()
