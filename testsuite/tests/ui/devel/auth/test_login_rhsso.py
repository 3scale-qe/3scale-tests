"""Rewrite of spec/ui_specs/developer_portal/ tests"""

import pytest

from testsuite.ui.views.admin.audience.developer_portal.sso_integrations import (
    RHSSOIntegrationEditView,
    RHSSOIntegrationDetailView,
)
from testsuite.ui.views.devel import BaseDevelView


@pytest.fixture(scope="module")
def rhsso_integration(request, threescale, testconfig, custom_admin_login, navigator):
    """
    Due to the fact that once you create sso integration you can't delete it only edit it,
    this workaround is needed to simplify UI test
    """
    rhsso = [x for x in threescale.dev_portal_auth_providers.list() if x["kind"] == "keycloak"]
    if not rhsso:
        rhsso = [
            threescale.dev_portal_auth_providers.create(
                {"kind": "keycloak", "client_id": "tmp", "client_secret": "tmp", "site": "https://anything.invalid"}
            )
        ]

    if not testconfig["skip_cleanup"]:

        def _delete():
            custom_admin_login()
            sso_edit = navigator.navigate(RHSSOIntegrationDetailView, integration=rhsso[0])
            sso_edit.publish_checkbox.check(False)

        request.addfinalizer(_delete)

    return rhsso[0]


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(custom_admin_login, navigator, rhsso_service_info, rhsso_integration):
    """Setup for RHSSO integration"""
    custom_admin_login()
    sso = navigator.navigate(RHSSOIntegrationEditView, integration=rhsso_integration)

    admin = rhsso_service_info.realm.admin
    client_id = rhsso_service_info.client.client_id
    client = admin.get_client(client_id)["clientId"]
    client_secret = admin.get_client_secrets(client_id)["value"]
    sso.edit(client, client_secret, rhsso_service_info.issuer_url())

    sso = navigator.navigate(RHSSOIntegrationDetailView, integration=rhsso_integration)
    admin.update_client(client_id, payload={"standardFlowEnabled": True, "redirectUris": [sso.callback_url()]})
    sso.publish()

    return admin.get_user(rhsso_service_info.user)


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7633")
def test_devel_login_rhsso(custom_devel_rhsso_login, navigator, testconfig, rhsso_setup):
    """
    Test:
        - Login into developer portal via RHSSO
        - Assert that login was successful
    """
    test_user = testconfig["rhsso"]["test_user"]
    custom_devel_rhsso_login(test_user["username"], test_user["password"], rhsso_setup["username"])
    devel_view = BaseDevelView(navigator.browser)
    assert devel_view.is_displayed
    assert devel_view.is_logged_in
