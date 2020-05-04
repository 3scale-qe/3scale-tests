"""HttpClient for Service mesh"""
import requests
from threescale_api.utils import HttpClient


class ServiceMeshHttpClient(HttpClient):
    """HttpClient for Service mesh"""

    # pylint: disable=too-many-arguments
    def __init__(self, app, session, verify, root_path, openshift, root_url):
        self.openshift = openshift
        self.root_url = root_url
        self.root_path = root_path
        super().__init__(app, "endpoint", session, verify)

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        path = self.root_path + "/" + path
        return super().request(method, path, **kwargs)

    @property
    def _base_url(self) -> str:
        return self.root_url
