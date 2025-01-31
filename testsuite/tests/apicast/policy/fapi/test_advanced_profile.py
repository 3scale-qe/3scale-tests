from enum import verify

import pytest

from testsuite import rawobj
from testsuite.rhsso import RHSSO, RHSSOServiceConfiguration
from testsuite.tests.apicast.policy.fapi.headers import Headers
from testsuite.ui.views.admin.product.integration.policies import Policies
from keycloak import KeycloakOpenID
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.utils import warn_and_skip, blame


@pytest.fixture(scope="module")
def service(service):
    """
    todo

    policy order:
        3scale APIcast
        Fapi
        Logging
    """
    mtls_policy = rawobj.PolicyConfig(Policies.OAUTH_TWO_MUTUAL_TLS_CLIENT_AUTHENTICATION.value, configuration = {})
    fapi_policy = rawobj.PolicyConfig("fapi", configuration = {
        "validate_x_fapi_customer_ip_address": True,
        "validate_oauth2_certificate_bound_access_token": True
      })
    # logging_policy = rawobj.PolicyConfig("logging", {
    #     "enable_access_logs": False,
    #     # "custom_logging": '\"{{request}}\" to service {{service.id}} and {{service.serializable.name}} with request fapi ID: \"{{req.headers.x-fapi-transaction-id}}\" and response fapi ID: \"{{res.headers.x-fapi-transaction-id}}\" \"{{res.headers.server}}\"'}
    #     "custom_logging": f'{{{{req.headers.{Headers.TRANSACTION_ID.value}}}}}#{{{{resp.headers.{Headers.TRANSACTION_ID.value}}}}}'}
    #     )
    # service.proxy.list().policies.insert(1, mtls_policy)
    service.proxy.list().policies.insert(2, fapi_policy)
    return service




def get_client_uuid(client_id, admin_client):  # todo dat tuhle funkci do Client v objects?
    clients = admin_client.get_clients()
    return next((client['id'] for client in clients if client['clientId'] == client_id), None)



# @pytest.fixture(scope="module")
# def mtls_sso_service_info(rhsso_service_info):
#     admin = rhsso_service_info.client.realm.admin  # todo client toho hodne zvladne, neslo by to nastavovani udelat elegantneji?
#     client = rhsso_service_info.client.oidc_client
#
#     client_uuid = get_client_uuid(client.client_id, admin)
#
#     client_repr = admin.get_client(client_uuid)
#
#     client_repr.update({"directAccessGrantsEnabled": True})
#
#     client_repr["attributes"].update({
#         "tls.client.certificate.bound.access.tokens": "true",  # Enables mTLS certificate-bound tokens
#         "client.authentication.type": "tls",  # Requires TLS client authentication
#         "token.endpoint.auth.method": "tls_client_auth",  # OAuth2 mTLS authentication
#         # "tls.client.auth.subject.dn": "CN=my-client,O=My Organization,C=US"  # Client certificate DN
#     })
#
#     # # Enable FAPI Compliance
#     # client["attributes"].update({
#     #     "fapi.compliance.enabled": "true",  # Enforces FAPI security profile
#     #     "fapi.compliance.profile": "FAPI1Advanced"  # Choose FAPI1 or FAPI1Advanced
#     # })
#
#     # Update the client
#     admin.update_client(client_uuid, client_repr)
#     return rhsso_service_info




#
#

#curl -k -v -H "Content-Type: application/x-www-form-urlencoded" \
   # -d 'grant_type=client_credentials' \
   # -d 'client_id=mtls_client_demo' \
   # --cert client.crt \
   # --key client.key \
   # --cacert rootCA.pem \
   # "https://keycloak:9443/realms/basic/protocol/openid-connect/token"

@pytest.fixture(scope="module")
#def tmp_mtls_client(mtls_sso_service_info, certificate):
def tmp_mtls_client():
# todo

#     return mtls_sso_service_info.client.mtls_client(
#         cert=("/home/mstastny/fapi/client.crt", "/home/mstastny/fapi/client.key"),
#         verify="/home/mstastny/fapi/client.key",
#
#     )

#     lokalni keycloak
#     return KeycloakOpenID(
#         server_url="https://keycloak:9443/",
#         client_id='mtls_client_demo',
#         realm_name='basic',
#         cert=("/home/mstastny/fapi/client.crt", "/home/mstastny/fapi/client.key"),
#         verify="/home/mstastny/fapi/rootCA.pem",
#     )

    return KeycloakOpenID(
        server_url="https://ssl-rhbk-mstastny-foo.apps.ocp-cluster.osp.api-qe.eng.rdu2.redhat.com",
        client_id='mtls_client',
        realm_name='basic',
        cert=("/home/mstastny/Repos/rh/gitlab/3scale-qe/testsuite-tools/tools/base/rhbk/secrets/client.crt", "/home/mstastny/Repos/rh/gitlab/3scale-qe/testsuite-tools/tools/base/rhbk/secrets/client.key"),
        verify="/home/mstastny/Repos/rh/gitlab/3scale-qe/testsuite-tools/tools/base/rhbk/secrets/rootCA.pem",
    )
#"https://keycloak:9443/realms/basic/protocol/openid-connect/token"


# @pytest.fixture(scope="module")
# def mtls_client(mtls_sso_service_info, certificate):
# # todo
#     return mtls_sso_service_info.client.mtls_client(cert=(certificate.files["certificate"], certificate.files["key"]))
#
# # zjistit jak udelat certifikatu ca
# # potreba najit zpusob jak upravit klienta, aby dostal key- value certifikat
# # potreba pohledat, jestli testsuita ma nejake predchystane certifikaty (myslim ze jsem neco odobneho videl)
# # certifikacni autoritu pro dany certifikat narvat i do keycloaku
#
#
# #
# #
#
#
#
# #
# #
# #
# #
# #
# #
#
# @pytest.fixture(scope="module")
# def staging_client(api_client):
#     """
#     Staging client
#     The auth of the session is set up to none in order to test different auth methods
#     The auth of the request will be passed in test functions
#     """
#     client = api_client()
#     client.auth = None
#     return client
# #
# #
# # @pytest.fixture(scope="module")
# # def production_client(prod_client):
# #     """
# #     Production client
# #     The auth of the session is set up to none in order to test different auth methods
# #     The auth of the request will be passed in test functions
# #     """
# #     client = prod_client()
# #     client.auth = None
# #     return client
# #
# #
#
#
# def _resolve_rhsso(testconfig, tools, rhsso_kind):
#     cnf = testconfig["rhsso"]
#     if "password" not in cnf:
#         return None
#     key = "no-ssl-rhbk"
#     if rhsso_kind == "rhsso":
#         key = "no-ssl-sso"
#     return RHSSO(server_url=tools[key], username=cnf["username"], password=cnf["password"])
#
#
# @pytest.fixture(scope="module")
# def rhsso_service_info(request, testconfig, tools, rhsso_kind):
#     """
#     Set up client for zync
#     :return: dict with all important details
#     """
#     rhsso = RHSSO(server_url="https://ssl-rhbk-mstastny-foo.apps.ocp-cluster.osp.api-qe.eng.rdu2.redhat.com", username="admin", password="GreenPanda48")  # todo
#     if not rhsso:
#         warn_and_skip("SSO admin password neither discovered not set in config", "fail")
#     realm = rhsso.create_realm(blame(request, "realm"), accessTokenLifespan=24 * 60 * 60)
#
#     if not testconfig["skip_cleanup"]:
#         request.addfinalizer(realm.delete)
#
#     client = realm.create_client(
#         name=blame(request, "client"),
#         serviceAccountsEnabled=True,
#         directAccessGrantsEnabled=True,
#         publicClient=False,
#         protocol="openid-connect",
#         standardFlowEnabled=True
#     )
#
#     cnf = testconfig["rhsso"]
#     username = cnf["test_user"]["username"]
#     password = cnf["test_user"]["password"]
#     user = realm.create_user(username, password)
#
#     client.assign_role("manage-clients")
#
#     return RHSSOServiceConfiguration(rhsso, realm, client, user, username, password)
#
#
# @pytest.fixture(scope="module", autouse=True)
# def rhsso_setup(lifecycle_hooks, rhsso_service_info):
#     """
#     Have application/service with RHSSO auth configured
#     Sets the credentials_location to basic auth
#     """
#     lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info, credentials_location="authorization"))
#     return rhsso_service_info




def test_fapi_realm(tmp_mtls_client, api_client):
    res = tmp_mtls_client.token(grant_type="client_credentials")

    foo = "dsd"
    client = api_client(cert=("/home/mstastny/Repos/rh/gitlab/3scale-qe/testsuite-tools/tools/base/rhbk/secrets/client.crt", "/home/mstastny/Repos/rh/gitlab/3scale-qe/testsuite-tools/tools/base/rhbk/secrets/client.key"), verify=False)
    response = client.get("/get", headers={"authorization": "Bearer " + res["access_token"]})

    api_client = api_client()

    api_client.auth = None
    api_client


    y = mtls_sso_service_info.client.oidc_client.client_id
    y = mtls_sso_service_info.realm.name

    assert 1 == 1


