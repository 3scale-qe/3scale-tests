"""
Rewrite of spec/functional_specs/auth/rhsso/openid_rhsso_flows_spec.rb

The test is focused on the synchronization between 3scale system/zync components with RHSSO.
The main idea of this test is to change each flow of the oidc 3scale service
and check RHSSO client (client for 3scale application) if the flows are changed in the RHSSO client.

After the flow of the service is changed,
you need to update the application in order to trigger zync to update the flow on the RHSSO.
https://issues.redhat.com/browse/THREESCALE-3025
"""

import backoff
import pytest
from threescale_api.resources import Service

from testsuite.rhsso import OIDCClientAuth
from testsuite.utils import blame_desc


pytestmark = [
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1948"),
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1949"),
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1951"),
]


DEFAULT_FLOWS = {
    "implicit_flow_enabled": False,
    "standard_flow_enabled": False,
    "direct_access_grants_enabled": False,
    "service_accounts_enabled": False,
}


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to OIDC"
    service_settings.update(backend_version=Service.AUTH_OIDC)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(rhsso_service_info, service_proxy_settings):
    "Set OIDC issuer and type"
    service_proxy_settings.update(
        oidc_issuer_endpoint=rhsso_service_info.authorization_url(), oidc_issuer_type="keycloak"
    )
    return service_proxy_settings


@pytest.fixture(scope="module")
def service(service):
    """Updates OIDC configuration to default flows (each flow is set to false)"""
    service.proxy.oidc.update(params={"oidc_configuration": DEFAULT_FLOWS})
    return service


@pytest.fixture(scope="module")
def application(rhsso_service_info, application):
    "Add OIDC client authentication"
    application.register_auth("oidc", OIDCClientAuth.partial(rhsso_service_info))
    return application


def change_flows(application, flow_to_update, request):
    """
    Changes flows to given application
    :param application: application
    :param flow_to_update: flows to update
    :return: updated application
    """
    params = {**DEFAULT_FLOWS, **flow_to_update}
    update = application.service.proxy.oidc.update(params={"oidc_configuration": params})
    application["description"] = blame_desc(request, "description")
    application.update()
    return update


# Zync is sometimes too slow to update the RHSSO client.
@backoff.on_exception(backoff.fibo, Exception, max_tries=8, jitter=None)
def get_flows(realm, client_id, expected_flow, expected_value):
    """
    Retries until the changed flows appear on the RHSSO side.
    Expected flows are in the TESTING_FLOWS global variable.
    :param rhsso_client: Rhsso client to get flows from
    :return: dictionary with flows
    """

    rhsso_client = realm.admin.get_client(client_id)

    flows = {
        "implicit_flow_enabled": rhsso_client["implicitFlowEnabled"],
        "standard_flow_enabled": rhsso_client["standardFlowEnabled"],
        "direct_access_grants_enabled": rhsso_client["directAccessGrantsEnabled"],
        "service_accounts_enabled": rhsso_client["serviceAccountsEnabled"],
    }

    if flows[expected_flow] != expected_value:
        raise ValueError(f"Flow {expected_flow} was not changed, expected {expected_value} got {flows[expected_flow]}")
    return flows


@pytest.mark.parametrize(
    "flow_type,expected",
    [
        ("implicit_flow_enabled", (True, False, False, False)),
        ("standard_flow_enabled", (False, True, False, False)),
        ("direct_access_grants_enabled", (False, False, True, False)),
        ("service_accounts_enabled", (False, False, False, True)),
    ],
)
def test(application, rhsso_service_info, request, flow_type, expected):
    """
    Test checks if the change of the flows of 3scale service were reflected on
    the RHSSO client for 3scale application.
    """

    result = change_flows(application, {flow_type: True}, request)
    assert result is not None

    client_id = rhsso_service_info.get_application_client(application)
    flows = get_flows(rhsso_service_info.realm, client_id, flow_type, True)

    assert flows["implicit_flow_enabled"] is expected[0]
    assert flows["standard_flow_enabled"] is expected[1]
    assert flows["direct_access_grants_enabled"] is expected[2]
    assert flows["service_accounts_enabled"] is expected[3]
