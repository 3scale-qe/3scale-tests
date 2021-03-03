"""
Utility resources for RHSSO manipulation
"""

import functools

from keycloak.admin.clients import Client
from keycloak.admin.realm import Realm
from keycloak.admin.users import User
from keycloak.openid_connect import KeycloakOpenidConnect
from keycloak.exceptions import KeycloakClientError

from threescale_api.auth import BaseClientAuth
from threescale_api.resources import Service
from threescale_api.utils import HttpClient

from testsuite.httpx import HttpxOidcClientAuth
from testsuite.rhsso.realm import RetryKeycloakRealm


class OIDCClientAuthHook:
    """Configure rhsso auth through app hooks"""

    def __init__(self, rhsso_service_info, credentials_location="authorization", oidc_configuration=None):
        self.rhsso_service_info = rhsso_service_info
        self.credentials_location = credentials_location
        self.oidc_configuration = oidc_configuration
        if self.oidc_configuration is None:
            self.oidc_configuration = {
                "standard_flow_enabled": False,
                "direct_access_grants_enabled": True}

    # pylint: disable=no-self-use
    def before_service(self, service_params: dict) -> dict:
        """Update service params"""
        service_params.update(backend_version=Service.AUTH_OIDC)
        return service_params

    # pylint: disable=unused-argument
    def before_proxy(self, service: Service, proxy_params: dict):
        """Update proxy params"""
        proxy_params.update(
            credentials_location=self.credentials_location,
            oidc_issuer_endpoint=self.rhsso_service_info.authorization_url(),
            oidc_issuer_type="keycloak")
        return proxy_params

    # pylint: disable=no-self-use
    def on_service_create(self, service):
        """Update oidc config"""

        service.proxy.oidc.update(params={"oidc_configuration": self.oidc_configuration})

    def on_application_create(self, application):
        """Register OIDC auth object for api_client"""

        # pylint: disable=protected-access
        if application._client_factory is HttpClient:
            application.register_auth(
                "oidc", OIDCClientAuth.partial(self.rhsso_service_info, location=self.credentials_location))
        else:
            application.register_auth(
                "oidc", HttpxOidcClientAuth.partial(self.rhsso_service_info, location=self.credentials_location))


class RHSSO:
    """Helper class for RHSSO server"""

    def __init__(self, server_url, username, password) -> None:
        self.server_url = server_url
        self.realm = RetryKeycloakRealm(server_url=server_url, realm_name='master')
        self.oidc = KeycloakOpenidConnect(realm=self.realm, client_id="admin-cli", client_secret=None)
        self.admin = self.realm.admin
        self.credentials = (username, password)
        self.refresh_token()

    def refresh_token(self):
        """Request and reset admin token"""
        username, password = self.credentials
        self.token = self.oidc.password_credentials(username=username, password=password)
        self.admin.set_token(self.token)

    def create_realm(self, name: str, **kwargs) -> Realm:
        """Creates new realm"""
        return self.admin.realms.create(name=name, enabled=True, sslRequired="None", **kwargs)

    def create_oidc_client(self, realm, client_id, secret):
        """Creates OIDC client"""
        keycloak_realm = RetryKeycloakRealm(server_url=self.server_url, realm_name=realm.realm)
        return KeycloakOpenidConnect(realm=keycloak_realm, client_id=client_id, client_secret=secret)

    # pylint: disable=too-many-arguments
    def password_authorize(self, realm, client_id, secret, username, password):
        """Returns token retrieved by password authentication"""
        oidc = self.create_oidc_client(realm, client_id, secret)
        return oidc.password_credentials(username=username, password=password)


# pylint: disable=too-few-public-methods
class RHSSOUser:
    """
    Wrapper for RHSSO user and its username and password combination
    """

    def __init__(self, user: User, username: str, password: str) -> None:
        self.user = user
        self.username = username
        self.password = password

    def logout(self):
        """
        Logs the user out
        """
        self.user.logout()


class RHSSOServiceConfiguration:
    """
    Wrapper for all information that tests need to know about RHSSO
    """

    def __init__(self, rhsso: RHSSO, realm: Realm, client: Client, user: RHSSOUser) -> None:
        self.rhsso = rhsso
        self.realm = realm
        self.user = user.user
        self.client = client
        self.username = user.username
        self.password = user.password
        self._oidc_client = None

    @property
    def oidc_client(self):
        """OIDCClient for the created client"""
        if not self._oidc_client:
            secret = self.client.secret["value"]
            client_id = self.client.id
            self._oidc_client = self.rhsso.create_oidc_client(self.realm, client_id, secret)
        return self._oidc_client

    def issuer_url(self) -> str:
        """
        Returns issuer url for 3scale in format
        http(s)://<HOST>:<PORT>/auth/realms/<REALM_NAME>
        :return: url
        """
        return self.oidc_client.get_url("issuer")

    def jwks_uri(self):
        """
        Returns jwks uri for 3scale in format
        http(s)://<HOST>:<PORT>o/auth/realms/<REALM_NAME>/protocol/openid-connect/certs
        :return: url
        """
        return self.oidc_client.get_url("jwks_uri")

    def authorization_url(self) -> str:
        """
        Returns authorization url for 3scale in format
        http(s)://<CLIENT_ID>:<CLIENT_SECRET>@<HOST>:<PORT>/auth/realms/<REALM_NAME>
        :return: url
        """
        try:
            secret = self.client.secret["value"]
        except KeycloakClientError:
            self.rhsso.refresh_token()
            secret = self.client.secret["value"]
        client_id = self.client.id
        url = self.issuer_url()
        return url.replace("://", "://%s:%s@" % (client_id, secret), 1)

    def password_authorize(self, client_id, secret):
        """Returns token retrived by password authentication"""
        return self.rhsso.password_authorize(self.realm, client_id, secret, self.username, self.password)

    def token_url(self) -> str:
        """
        Returns token endpoint url
        http(s)://<HOST>:<PORT>/auth/realms/<REALM_NAME>/protocol/openid-connect/token
        :return: url
        """
        return self.oidc_client.get_url("token_endpoint")

    def body_for_token_creation(self, app) -> str:
        """
        Returns body for creation of token
        :return: body
        """
        app_key = app.keys.list()["keys"][0]["key"]["value"]
        app_id = app["client_id"]
        return f"grant_type=password&client_id={app_id}&client_secret={app_key}" \
               f"&username={self.username}&password={self.password}"

    def access_token(self, app) -> str:
        """
        Returns access token for given application
        :param app: 3scale application
        :return: access token
        """
        app_key = app.keys.list()["keys"][0]["key"]["value"]
        return self.password_authorize(app["client_id"], app_key).token['access_token']


# pylint: disable=too-few-public-methods
class OIDCClientAuth(BaseClientAuth):
    """Authentication class for  OIDC based authorization"""

    @classmethod
    def partial(cls, service_rhsso_info, **kwargs):
        """Returns partially "initialized instance" with interface suitable for register_auth"""

        return functools.partial(cls, service_rhsso_info, **kwargs)

    def __init__(self, service_rhsso_info, application, location=None) -> None:
        super().__init__(application, location)

        self.app_key = application.keys.list()["keys"][0]["key"]["value"]
        self.token = service_rhsso_info.password_authorize(application["client_id"], self.app_key)

    def __call__(self, request):
        access_token = self.token()
        credentials = {"access_token": access_token}

        if self.location == "authorization":
            request.headers.update({'Authorization': 'Bearer ' + access_token})
        elif self.location == "headers":
            request.prepare_headers(credentials)
        elif self.location == "query":
            request.prepare_url(request.url, credentials)
        else:
            raise ValueError("Unknown credentials location '%s'" % self.location)
        return request


def add_realm_management_role(role_name, client, realm):
    """Add realm management role to the client"""
    user = client.service_account_user
    realm_management = realm.clients.by_client_id('realm-management')
    role = realm_management.roles.by_name(role_name)
    user.role_mappings.client(realm_management).add([role.entity])


def create_rhsso_user(realm, username, password):
    "Creates new user in RHSSO"
    user = realm.users.create(username, enabled=True)
    user.reset_password(password, temporary=False)
    return RHSSOUser(user, username, password)
