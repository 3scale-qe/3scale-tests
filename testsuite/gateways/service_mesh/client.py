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

    # pylint: disable=too-many-locals
    def request(self, method, path, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None,
                json=None) -> requests.Response:
        path = self.root_path + "/" + path
        return super().request(method, path, params, data, headers, cookies, files, auth, timeout, allow_redirects,
                               proxies, hooks, stream, json)

    @property
    def _base_url(self) -> str:
        return self.root_url
