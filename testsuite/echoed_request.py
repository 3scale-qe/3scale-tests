"""
Shadow request classes to unify workflow over different backends
e.g httpbin-go returns headers 'Host': ["httpbingo.org"], but httpbin returns 'Host': "httpbin.org"
"""
from urllib.parse import urlparse

import requests
from dynaconf import settings
from requests.structures import CaseInsensitiveDict


class EchoedRequest:  # pylint: disable=too-few-public-methods
    """Default wrapper over backend"""

    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.json = response.json()
        self.headers: CaseInsensitiveDict = CaseInsensitiveDict(data=self.json.get("headers"))
        self.params = self.json.get("args")
        self.body = self.json.get("body")
        self.path = self.json.get("path")

    @staticmethod
    def create(response: requests.Response):
        """Factory method to create different backends"""
        url = EchoedRequest.__get_url(response)
        if url == _PrimaryRequest.base_hostname():
            return _PrimaryRequest(response)
        if url == _HttpbinRequest.base_hostname():
            return _HttpbinRequest(response)
        if url == _EchoApiRequest.base_hostname():
            return _EchoApiRequest(response)
        if url == _HttpbinGoRequest.base_hostname():
            return _HttpbinGoRequest(response)

        return EchoedRequest(response)

    @staticmethod
    def __get_url(response: requests.Response) -> str:
        """Gets URL from response"""
        headers = response.json()["headers"]
        url = headers.get('HTTP_HOST') or headers.get('Host')
        if isinstance(url, list):
            url = url[0]
        return url

    @staticmethod
    def _base_hostname(kind):
        """Returns hostname for specific backend"""
        url = settings["threescale"]["service"]["backends"][kind]
        return urlparse(url).hostname


class _PrimaryRequest(EchoedRequest):
    """Wrapper over Primary backend"""

    @staticmethod
    def base_hostname():
        """Returns hostname for primary backend"""
        return EchoedRequest._base_hostname("primary")


class _HttpbinRequest(EchoedRequest):
    """Wrapper over Primary backend"""

    @staticmethod
    def base_hostname():
        """Returns hostname for httpbin backend"""
        return EchoedRequest._base_hostname("httpbin")


class _EchoApiRequest(EchoedRequest):
    """Wrapper over Echo api backend"""

    def __init__(self, response: requests.Response) -> None:
        super().__init__(response)
        self.headers = self.__process_headers()

    @staticmethod
    def base_hostname():
        """Returns hostname for echo api backend"""
        return EchoedRequest._base_hostname("echo-api")

    def __process_headers(self) -> CaseInsensitiveDict:
        headers = self.headers
        http_header_keys = filter(lambda x: x.startswith("HTTP_"), list(self.headers.keys()))
        for key in http_header_keys:
            new_key = key.replace("HTTP_", "").replace("_", "-")
            headers[new_key] = headers[key]
        return CaseInsensitiveDict(headers)


class _HttpbinGoRequest(EchoedRequest):
    """Wrapper over Httpbin go backend"""

    def __init__(self, response: requests.Response) -> None:
        super().__init__(response)
        self.headers = self.__process_headers()
        self.params = self.__process_params()

    @staticmethod
    def base_hostname():
        """Returns hostname for httpbin go backend"""
        return EchoedRequest._base_hostname("httpbin-go")

    def __process_params(self) -> CaseInsensitiveDict:
        params = self.params
        for key in params:
            if isinstance(params[key], list) and len(params[key]) == 1:
                params[key] = params[key][0]
        return CaseInsensitiveDict(data=params)

    def __process_headers(self) -> CaseInsensitiveDict:
        headers = self.headers
        for key in headers:
            if isinstance(headers[key], list):
                headers[key] = ",".join(headers[key])
        return CaseInsensitiveDict(data=headers)
