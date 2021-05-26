"""Http client with HTTPX library supporting HTTP/1.1 and HTTP/2"""
import functools
import logging
from typing import Iterable, Generator

from httpx import Client, Request, Response, URL, Auth, create_ssl_context
from threescale_api.resources import Application, Service
from threescale_api.utils import response2str, request2curl
import backoff

from testsuite.lifecycle_hook import LifecycleHook


# pylint: disable=too-few-public-methods
from testsuite.utils import basic_auth_string


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def _log_request(request):
    """log request details"""
    class Request:
        """attribute body/url is needed"""
        def __init__(self, request):
            self.__request = request
            self.body = "".join([i.decode("utf-8") for i in request.stream])
            self.url = str(request.url)

        def __getattr__(self, name):
            return getattr(self.__request, name)

    log.info("[CLIENT]: %s", request2curl(Request(request)))


def _log_response(response):
    """log response details"""
    class Response:
        """attr reason is needed"""
        def __init__(self, response):
            self.__response = response
            self.reason = response.reason_phrase

        def __getattr__(self, name):
            return getattr(self.__response, name)

    log.info("\n".join(["[CLIENT]:", response2str(Response(response))]))


class UnexpectedResponse(Exception):
    """Slightly different response attributes were expected"""
    def __init__(self, msg, response):
        super().__init__(msg)
        self.response = response


class HttpxHook(LifecycleHook):
    """Lifecycle hook for Httpx client"""

    def __init__(self, http2: bool = False) -> None:
        self.http2 = http2

    def on_application_create(self, application: Application):
        # pylint: disable=protected-access
        application._client_factory = HttpxClient.partial(self.http2)
        application.register_auth(Service.AUTH_USER_KEY, HttpxUserKeyAuth)
        application.register_auth(Service.AUTH_APP_ID_KEY, HttpxAppIdKeyAuth)


# pylint: disable=too-many-arguments, too-many-instance-attributes
class HttpxClient:
    """Api client class that is using HTTPX library instead of requests"""

    @classmethod
    def partial(cls, http2, **kwargs):
        """Returns partially initialized HttpxClient suitable for client in the application"""
        return functools.partial(cls, http2, **kwargs)

    def __init__(self, http2, app, endpoint: str = "sandbox_endpoint",
                 verify: bool = None, cert=None, disable_retry_status_list: Iterable = ()) -> None:
        self._app = app
        self._endpoint = endpoint
        self._status_forcelist = {503, 404} - set(disable_retry_status_list)
        self._verify = verify
        self._cert = cert
        self.auth = app.authobj()
        self.http2 = http2
        self._client = Client(base_url=self._base_url, verify=self._ssl_context(), http2=http2)
        self._client.event_hooks["request"] = [_log_request]
        self._client.event_hooks["response"] = [_log_response]

    def close(self):
        """Close httpx client"""
        self._client.close()

    @property
    def _base_url(self) -> str:
        """Determine right url at runtime"""
        return self._app.service.proxy.fetch()[self._endpoint]

    def _ssl_context(self):
        """Create ssl context for httpx"""
        return create_ssl_context(cert=self._cert, verify=self._verify, http2=self.http2, trust_env=True)

    def extend_connection_pool(self, maxsize: int):
        """
        Extend connection pool
        This method is needed for compatibility with HttpClient
        """

    @backoff.on_exception(backoff.fibo, UnexpectedResponse, max_tries=8, jitter=None)
    def request(self, method, path,
                content=None, data=None, files=None, json=None,
                params=None, headers=None, cookies=None,
                auth=None, allow_redirects=True, timeout=None):
        """mimics requests interface"""
        auth = auth or self.auth
        self._client.auth = auth

        response = self._client.request(
            method=method,
            url=path,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            allow_redirects=allow_redirects,
            timeout=timeout)

        if response.status_code in self._status_forcelist:
            raise UnexpectedResponse(f"Didn't expect '{response.status_code}' status code", response)

        return response

    def get(self, *args, **kwargs):
        """mimics requests interface"""
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        """mimics requests interface"""
        return self.request('POST', *args, **kwargs)

    def patch(self, *args, **kwargs):
        """mimics requests interface"""
        return self.request('PATCH', *args, **kwargs)

    def put(self, *args, **kwargs):
        """mimics requests interface"""
        return self.request('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        """mimics requests interface"""
        return self.request('DELETE', *args, **kwargs)


# pylint: disable=too-few-public-methods
class HttpxBaseClientAuth(Auth):
    """Base auth class for Httpx client"""

    def __init__(self, app, location=None):
        self.app = app
        self.location = location
        self.credentials = {}
        if location is None:
            self.location = app.service.proxy.list().entity["credentials_location"]

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        """Authenticates requests with 3scale credentials"""
        if self.location == 'authorization':
            key, value = self.credentials.values()
            request.headers['Authorization'] = basic_auth_string(key, value)
        elif self.location == 'headers':
            self._prepare_headers(request)
        elif self.location == 'query':
            request.url = URL(request.url, params=self.credentials)
        else:
            raise ValueError("Unknown credentials location '%s'" % self.location)

        yield request

    def _prepare_headers(self, request):
        for header in self.credentials.items():
            name, value = header
            request.headers[name] = value


# pylint: disable=too-few-public-methods
class HttpxUserKeyAuth(HttpxBaseClientAuth):
    """Auth class for Httpx client for product secured by user key"""

    def __init__(self, app, location=None):
        super().__init__(app, location)
        self.credentials = {
            self.app.service.proxy.list()["auth_user_key"]: self.app["user_key"]
        }

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        if self.location == 'authorization':
            key = list(self.credentials.values())[0]
            request.headers['Authorization'] = basic_auth_string(key, '')
            yield request
        else:
            yield from super().auth_flow(request)


# pylint: disable=too-few-public-methods
class HttpxAppIdKeyAuth(HttpxBaseClientAuth):
    """Auth class for Httpx client for product secured by app id and app key"""

    def __init__(self, app, location=None):
        super().__init__(app, location)
        proxy = self.app.service.proxy.list()
        self.credentials = {
            proxy["auth_app_id"]: self.app["application_id"],
            proxy["auth_app_key"]: self.app.keys.list()["keys"][0]["key"]["value"]
        }


class HttpxOidcClientAuth(HttpxBaseClientAuth):
    """Auth class for Httpx client for product secured by oidc"""

    @classmethod
    def partial(cls, servifce_rhsso_info, **kwargs):
        """Returns partially "initialize instance" with interface suitable for register_auth"""
        return functools.partial(cls, servifce_rhsso_info, **kwargs)

    def __init__(self, service_rhsso_info, app, location=None) -> None:
        super().__init__(app, location)
        self.rhsso = service_rhsso_info
        self.token = self.rhsso.access_token(app)

    def _add_credentials(self, request: Request):
        if self.location == 'authorization':
            request.headers['Authorization'] = f"Bearer {self.token}"
        elif self.location == 'headers':
            request.headers['access_token'] = self.token
        elif self.location == 'query':
            request.url = URL(request.url, params={'access_token': self.token})
        else:
            raise ValueError("Unknown credentials location '%s'" % self.location)

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        self._add_credentials(request)
        response = yield request

        if response.status_code == 403:
            # Renew access token and try again
            self.token = self.rhsso.access_token(self.app)
            self._add_credentials(request)
            yield request
