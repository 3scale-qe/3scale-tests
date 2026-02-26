"""This module contains object wrappers on top of python-keycloak API, since that is not object based"""

from urllib.parse import urlparse

from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakPostError

from testsuite.config import settings


class Realm:
    """Helper class for RHSSO realm manipulation"""

    def __init__(self, master: KeycloakAdmin, name) -> None:
        self.admin = KeycloakAdmin(
            server_url=master.connection.server_url,
            username=master.connection.username,
            password=master.connection.password,
            realm_name=name,
            user_realm_name="master",
            verify=settings["ssl_verify"],
        )
        self.name = name

    def delete(self):
        """Deletes realm"""
        self.admin.delete_realm(self.name)

    def create_client(self, name, **kwargs):
        """Creates new client"""
        self.admin.create_client(payload={**kwargs, "clientId": name})
        client_id = self.admin.get_client_id(name)
        return Client(self, client_id)

    def create_user(self, username, password, **kwargs):
        """Creates new user"""
        kwargs["username"] = username
        kwargs["enabled"] = True
        kwargs.setdefault("firstName", "John")
        kwargs.setdefault("lastName", "Doe")
        kwargs["email"] = f"{username}@anything.invalid"
        self.admin.create_user(kwargs)
        user_id = self.admin.get_user_id(username)
        self.admin.set_user_password(user_id, password, temporary=False)
        self.admin.update_user(user_id, {"emailVerified": True})
        return user_id

    def oidc_client(self, client_id, client_secret) -> KeycloakOpenID:
        """Create OIDC client for this realm"""
        server_url = self.admin.connection.server_url

        # Inline check for server_url
        if server_url is None or not server_url.strip():
            raise RuntimeError("server_url must be set and non-empty")

        return KeycloakOpenID(
            server_url=server_url,
            client_id=client_id,
            realm_name=self.name,
            client_secret_key=client_secret,
        )


class Client:
    """Helper class for RHSSO client manipulation"""

    def __init__(self, realm: Realm, client_id) -> None:
        self.admin = realm.admin
        self.realm = realm
        self.client_id = client_id

    def assign_role(self, role_name):
        """Assign client role from realm management client"""
        user = self.admin.get_client_service_account_user(self.client_id)
        realm_management = self.admin.get_client_id("realm-management")
        role = self.admin.get_client_role(realm_management, role_name)
        self.admin.assign_client_role(user["id"], realm_management, role)

    @property
    def oidc_client(self) -> KeycloakOpenID:
        """OIDC client"""
        # Note This is different clientId (clientId) than self.client_id (Id), because RHSSO
        client_id = self.admin.get_client(self.client_id)["clientId"]
        secret = self.admin.get_client_secrets(self.client_id)["value"]
        return self.realm.oidc_client(client_id, secret)


# pylint: disable=too-few-public-methods
class RHSSO:
    """Helper class for RHSSO server"""

    def __init__(self, server_url, username, password, verify=None) -> None:
        # python-keycloak API requires url to be pointed at auth/ endpoint
        # pylint: disable=protected-access
        if verify is None:
            verify = settings["ssl_verify"]
        self.verify = verify
        try:
            self.master = KeycloakAdmin(
                server_url=server_url,
                username=username,
                password=password,
                realm_name="master",
                verify=verify,
            )
            self.master.get_clients()  # test whether the server url is valid
            self.server_url = server_url
        except KeycloakPostError:
            self.server_url = urlparse(server_url)._replace(path="auth/").geturl()
            self.master = KeycloakAdmin(
                server_url=self.server_url,
                username=username,
                password=password,
                realm_name="master",
                verify=verify,
            )
            self.master.get_clients()  # test whether the server url is valid

    def create_realm(self, name: str, **kwargs) -> Realm:
        """Creates new realm"""
        self.master.create_realm(payload={"realm": name, "enabled": True, "sslRequired": "None", **kwargs})
        return Realm(self.master, name)


# pylint: disable=too-few-public-methods
class Token:
    """
    Class for backwards compatibility for RHSSO token manipulation
    The right way is password_authorize()["access_token"],
    old way was password_authorize().token["access_token"]
    """

    def __init__(self, token) -> None:
        self.token = token

    def __getitem__(self, item):
        return self.token[item]
