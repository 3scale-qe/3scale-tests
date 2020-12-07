"""Custom KeyCloak resources for test suite"""
import requests
from keycloak.client import KeycloakClient
from keycloak.realm import KeycloakRealm
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class RetryKeycloakRealm(KeycloakRealm):
    """Keycloak Realm for use in testsuite, difference is that is the KeycloakClient it uses"""
    @property
    def client(self):
        if self._client is None:
            self._client = RetryKeycloakClient(server_url=self._server_url,
                                               headers=self._headers)
        return self._client


class RetryKeycloakClient(KeycloakClient):
    """KeycloakClient with retry"""
    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self._headers)
            self._retry_for_session(session=self._session)
        return self._session

    @staticmethod
    def _retry_for_session(session: requests.Session, total: int = 8):
        retry = Retry(
            total=total,
            backoff_factor=1,
            method_whitelist=False,
            status_forcelist=(503, 400, 403),
            raise_on_status=False,
            respect_retry_after_header=False
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
