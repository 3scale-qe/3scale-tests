# pylint: disable=too-few-public-methods,broad-except

"""
This provides interface to get test environment tools

Different sources can be used, e.g. if deployed in openshift tools can be gathered
from openshift namespace/project.

Historically "symbolic" names used as config keys in settings use name of
particular service e.g. 'httpbin'. This was never 100% accurate as the service
shouldn't represent a specific implementation but rather available upstream
API. It's better to think about these names as desired interface of the
upstream API. Even that is simplified, because all the services used as
upstream API have standardized interface thanks to EchoedRequest.

So 'httpbin' key doesn't represent the httpbin instance, but rather an upstream
API implementing calls of httpbin.

Note: It may be good idea to consider change of all these keys to something
abstract, however that would cause huge disruption in usage of the testsuite.
"""

# This uses direct access to testsuite settings and configuration objects. The
# difference is that this is integral part of the testsuite and has zero chance
# to become independent. IDEA: maybe it's worth to consider separation of that
# code that should be independent from testsuite

import inspect
import sys
from testsuite.config import settings
from testsuite.configuration import openshift
from testsuite.openshift.client import OpenShiftClient


_tr = {
    "echo_api": "mockserver+ssl",
    "httpbin": "go-httpbin+ssl",
    "httpbin_nossl": "go-httpbin",
    "httpbin_go": "go-httpbin+ssl",
    "httpbin_service": "go-httpbin+svc",
    "httpbin_go_service": "go-httpbin+svc",
    "jaeger": "jaeger-query",
}


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
        openshift.do_action("get", ["svc", key])  # just check if the service exists
        return f"http://{key}.{namespace}.svc:{port}"
    hostname = openshift.routes[key]["spec"]["host"]
    if option == "ssl":
        return f"https://{hostname}:443"
    return f"http://{hostname}:80"


class OpenshiftProject:
    """Get testenv tools from dedicated openshift namespace"""

    def __init__(self, namespace, server_url=None, token=None):
        self._cache = {}
        self._namespace = namespace
        if server_url and token:
            self._oc = OpenShiftClient(project_name=namespace, server_url=server_url, token=token)
        else:
            try:
                self._oc = openshift(project=namespace)
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
        if name in ["no-ssl-sso", "no-ssl-rhbk"]:
            return settings["rhsso"]["url"]
        try:
            return settings["threescale"]["service"]["backends"][name]
        except KeyError as err:
            if "+" in name or ":" in name:
                # env variable name can't contain '+' or ':', though keep the option
                # to pass the value via env
                name = name.replace("+", "_plus_").replace(":", "_port_")
                try:
                    return settings["threescale"]["service"]["backends"][name]
                except KeyError:  # pylint: disable=raise-missing-from
                    raise err
            raise err


class Rhoam(OpenshiftProject):
    """Read SSO from rhoam specific location"""

    def __init__(self):
        super().__init__("redhat-rhoam-user-sso")

    def __getitem__(self, name):
        if name not in ["no-ssl-sso", "no-ssl-rhbk"]:
            raise KeyError(name)
        # rhoam doesn't have http:// sso route
        return super().__getitem__("keycloak+ssl")


class Tools:
    """Initialize tools from various sources"""

    def __init__(self, sources, options):
        self_module = sys.modules[__name__]
        self._options = options
        self._sources = [self._init_source(getattr(self_module, t)) for t in sources]

    def __getitem__(self, name):
        for source in self._sources:
            try:
                value = source[name]
                if value is not None:
                    return value
            except Exception:
                pass
        raise KeyError(name)

    def _init_source(self, klass):
        """dynamic __init__ args introspection"""

        init_args = inspect.signature(klass.__init__).parameters.keys()
        init_args -= ["self", "args", "kwargs"]
        if len(init_args) == 0:
            return klass()
        init_args = {k: v for k, v in self._options.items() if k in init_args}
        if len(init_args) == 0:
            return klass()
        return klass(**init_args)
