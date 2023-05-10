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

        self.body = self.json.get("body", self.json.get("data"))
        self.path = self.json.get("path")

    @staticmethod
    def create(response: requests.Response):
        """Factory method to create different backends"""

        data = response.json()
        headers = data.get("headers", {})

        if "HTTP_HOST" in headers:
            return _EchoApiRequest(response)

        if "keepAlive" in data and "secure" in data:
            return _MockServerRequest(response)

        if "queryStringParameters" in data:
            return _MockServerRequest(response)

        if list in [type(i) for i in headers.values()]:
            return _HttpbinGoRequest(response)

        if list in [type(i) for i in data.get("args", {}) if len(i) == 1]:
            return _HttpbinGoRequest(response)

        return EchoedRequest(response)


class _EchoApiRequest(EchoedRequest):
    """Wrapper over Echo api backend"""

    def __init__(self, response: requests.Response) -> None:
        super().__init__(response)
        self.headers = self.__process_headers()
        if isinstance(self.params, str) and len(self.params) == 0:
            self.params = {}

    def __process_headers(self) -> CaseInsensitiveDict:
        headers = self.headers
        http_header_keys = filter(lambda x: x.startswith("HTTP_"), list(self.headers.keys()))
        for key in http_header_keys:
            new_key = key.replace("HTTP_", "").replace("_", "-")
            headers[new_key] = headers[key]
        return CaseInsensitiveDict(headers)


def _flatten(dict_):
    """Convert list values in dict to string values"""
    for k, val in dict_.items():
        if isinstance(val, list):
            dict_[k] = ",".join(val)
    return CaseInsensitiveDict(data=dict_)


def _flatten_single_params(params):
    """Httpbin returns single param/arg as string, let's follow this"""
    if params is None:
        return None
    params = params.copy()
    for k, val in params.items():
        if isinstance(val, list) and len(val) == 1:
            params[k] = val[0]
    return params


class _HttpbinGoRequest(EchoedRequest):
    """Wrapper over Httpbin go backend"""

    def __init__(self, response: requests.Response) -> None:
        super().__init__(response)
        self.headers = _flatten(self.headers)
        self.params = _flatten_single_params(self.params)
        if "url" in self.json:
            self.path = urllib.parse.urlparse(self.json["url"]).path
        elif "URL" in self.json:
            self.path = urllib.parse.urlparse(self.json["URL"]).path


class _MockServerRequest(EchoedRequest):
    """Wrapper over MockServer backend"""

    def __init__(self, response: requests.Response) -> None:
        super().__init__(response)
        self.headers = _flatten(self.headers)
        self.params = _flatten_single_params(self.json.get("queryStringParameters", {}))
