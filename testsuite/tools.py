# pylint: disable=too-few-public-methods,broad-except

"""This provides interface to get test environment tools

Different sources can be used, e.g. if deployed in openshift tools can be gathered
from openshift namespace/project."""

# This uses direct access to testsuite settings and configuration objects. The
# difference is that this is integral part of the testsuite and has zero chance
# to become independent. IDEA: maybe it's worth to consider separation of that
# code that should be independent from testsuite

from testsuite import CONFIGURATION
from testsuite.config import settings


_tr = {
    "echo_api": "echo-api+ssl",
    "httpbin": "httpbin+ssl",
    "httpbin_nossl": "httpbin",
    "httpbin_go": "go-httpbin+ssl",
    "httpbin_service": "httpbin+svc",
    "httpbin_go_service": "go-httpbin+svc",
    "jaeger": "jaeger-query"}


def _url(openshift, key, namespace):
    """helper to get right url"""

    key = _tr.get(key, key)
    option = ""
    if "+" in key:
        key, option = key.split("+", 1)
    if option.startswith("svc"):
        port = 8080
        if ":" in option:
            _, port = option.split(":", 1)
        return f"http://{key}.{namespace}.svc:{port}/"
    hostname = openshift.routes[key]["spec"]["host"]
    if option == "ssl":
        return f"https://{hostname}:443/"
    return f"http://{hostname}:80/"


class OpenshiftProject:
    """Get testenv tools from dedicated openshift namespace"""

    def __init__(self, namespace):
        self._cache = {}
        self._namespace = namespace
        try:
            self._oc = CONFIGURATION.openshift(project=namespace)
        except Exception:
            self._oc = None

    def __getitem__(self, name):
        if self._oc is None:
            raise KeyError(name)
        if name not in self._cache:
            try:
                self._cache[name] = _url(self._oc, name, self._namespace)
            except Exception as err:
                raise KeyError(name) from err

        return self._cache[name]


class Settings:
    """Get testenv tools from testsuite settings"""
    def __getitem__(self, name):
        return settings["threescale"]["service"]["backends"][name]
