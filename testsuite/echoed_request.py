"""
Shadow request classes to unify workflow over different backends
e.g httpbin-go returns headers 'Host': ["httpbingo.org"], but httpbin returns 'Host': "httpbin.org"
"""

# pylint: disable=too-few-public-methods

import urllib.parse

import requests
from requests.structures import CaseInsensitiveDict


class EchoedRequest:
    """Default wrapper over backend"""

    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.json = response.json()
        self.headers: CaseInsensitiveDict = CaseInsensitiveDict(data=self.json.get("headers"))
        self.params = self.json.get("args")

        # non-zero length string needs to be parsed and converted to dict
        # smells like bit of inconsistency, self.params should be of one type
        # instead of that few conversions happen. Something to fix in future
        if isinstance(self.params, str) and len(self.params) > 0:
            self.params = urllib.parse.parse_qs(self.params, keep_blank_values=True)
            for key in self.params:
                if isinstance(self.params[key], list) and len(self.params[key]) == 1:
                    self.params[key] = self.params[key][0]

        self.body = self.json.get("body")
        self.path = self.json.get("path")

    @staticmethod
    def create(response: requests.Response):
        """Factory method to create different backends"""

        data = response.json()

        if "HTTP_HOST" in data["headers"]:
            return _EchoApiRequest(response)

        if list in [type(i) for i in data["headers"].values()]:
            return _HttpbinGoRequest(response)

        if list in [type(i) for i in data["args"] if len(i) == 1]:
            return _HttpbinGoRequest(response)

        return EchoedRequest(response)


class _EchoApiRequest(EchoedRequest):
    """Wrapper over Echo api backend"""

    def __init__(self, response: requests.Response) -> None:
        super().__init__(response)
        self.headers = self.__process_headers()

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
