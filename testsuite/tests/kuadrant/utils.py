""" Utils and helpers for writing Kuadrant tests. """

from typing import Iterable
import logging
from urllib.parse import urljoin

import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import requests.auth
from threescale_api.utils import request2curl, response2str

logger = logging.getLogger(__name__)


class HttpClient:
    """3scale specific!!! HTTP Client

    This provides client to easily run api calls against provided service.
    Due to some delays in the infrastructure the client is configured to retry
    calls under certain conditions. To modify this behavior customized session
    has to be passed. session has to be fully configured in such case
    (e.g. including authentication"

    :param verify: SSL verification
    :param cert: path to certificate
    :param disable_retry_status_list:
        Iterable collection of status code that should not be retried by requests
    """

    def __init__(self, endpoint: str, verify: bool = None, cert=None, disable_retry_status_list: Iterable = ()):
        self._endpoint = endpoint
        self.verify = verify if verify is not None else False
        self.cert = cert
        self._status_forcelist = {503, 404} - set(disable_retry_status_list)
        self.session = self._create_session()

        logger.debug("[HTTP CLIENT] New instance: %s", self._base_url)

    def close(self):
        """Close requests session"""
        self.session.close()

    @staticmethod
    def retry_for_session(session: requests.Session, status_forcelist: Iterable, total: int = 8):
        """ Retry in case of status from `status_forcelist`."""
        retry = Retry(
            total=total,
            backoff_factor=1,
            status_forcelist=status_forcelist,
            raise_on_status=False,
            respect_retry_after_header=False
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

    @property
    def _base_url(self) -> str:
        """Determine right url at runtime"""
        # TODO determine right url from OCP
        return self._endpoint

    def _create_session(self):
        """Creates session"""
        session = requests.Session()
        self.retry_for_session(session, self._status_forcelist)
        return session

    def extend_connection_pool(self, maxsize: int):
        """Extend connection pool"""
        self.session.adapters["https://"].poolmanager.connection_pool_kw["maxsize"] = maxsize
        self.session.adapters["https://"].poolmanager.clear()

    def request(self, method, path,
                params=None, data=None, headers=None, cookies=None, files=None,
                auth=None, timeout=None, allow_redirects=True, proxies=None,
                hooks=None, stream=None, json=None) -> requests.Response:
        """mimics requests interface"""
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        url = urljoin(self._base_url, path)
        session = self.session
        session.auth = auth

        req = requests.Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            hooks=hooks,
        )
        prep = session.prepare_request(req)

        logger.info("[CLIENT]: %s", request2curl(prep))

        send_kwargs = {
            "timeout": timeout,
            "allow_redirects": allow_redirects
        }

        proxies = proxies or {}

        send_kwargs.update(
            session.merge_environment_settings(prep.url, proxies, stream, self.verify, self.cert))

        response = session.send(prep, **send_kwargs)

        logger.info("\n".join(["[CLIENT]:", response2str(response)]))

        return response

    def get(self, *args, **kwargs) -> requests.Response:
        """mimics requests interface"""
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs) -> requests.Response:
        """mimics requests interface"""
        return self.request('POST', *args, **kwargs)

    def patch(self, *args, **kwargs) -> requests.Response:
        """mimics requests interface"""
        return self.request('PATCH', *args, **kwargs)

    def put(self, *args, **kwargs) -> requests.Response:
        """mimics requests interface"""
        return self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs) -> requests.Response:
        """mimics requests interface"""
        return self.request('DELETE', *args, **kwargs)


class BaseClientAuth(requests.auth.AuthBase):
    """Abstract class for authentication of api client"""
    # pylint: disable=too-few-public-methods

    def __init__(self, location=None):
        self.location = location
        self.credentials = {}

    def __call__(self, request):
        credentials = self.credentials

        if self.location == "headers":
            heads = request.headers
            heads.update(credentials)
            request.prepare_headers(heads)
        elif self.location == "query":
            request.prepare_url(request.url, credentials)
        else:
            raise ValueError("Unknown credentials location '%s'" % self.location)

        return request


class UserKeyAuth(BaseClientAuth):
    """Provides user_key authentication for api client calls"""
    # pylint: disable=too-few-public-methods

    def __init__(self, key, location=None):
        super().__init__(location)
        self.credentials = {
            'Authorization': 'APIKEY ' + key
        }

    def __call__(self, request):
        if self.location == "authorization":
            auth = requests.auth.HTTPBasicAuth(next(iter(self.credentials.values())), "")
            return auth(request)
        return super().__call__(request)
