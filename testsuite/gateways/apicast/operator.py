"""Apicast deployed with ApicastOperator"""
import re
import time
from typing import Dict, Callable, Pattern, Any, Match, Union

from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.crd.apicast import APIcast
from testsuite.openshift.env import Properties

from .selfmanaged import SelfManagedApicast

StrMatcher = Dict[str, Union[str, Callable[[APIcast, Any], Any]]]
RegexMatcher = Dict[Pattern, Callable[[APIcast, Match, Any], Any]]


def apicast_service_list(apicast: APIcast, services: str):
    """Sets APICAST_SERVICE_LIST in the APIcast CR """
    service_list = str(services).split(",")
    apicast["enabledServices"] = service_list


def set_configuration_version(apicast: APIcast, match: Match, version):
    """Sets the configuration version the APIcast should use for this service"""
    service_id = match.group(1)
    overrides = apicast.model.spec.setdefault("serviceConfigurationVersionOverride", {})
    overrides[service_id] = str(version)


class OperatorEnviron(Properties):
    """
    Implements Properties for use in Operator and
    transforms APIcast environmental variables into operator properties
    """
    def __init__(self, apicast: APIcast, wait_function) -> None:
        self.apicast = apicast
        self.wait_function = wait_function

    NAMES: StrMatcher = {
        "APICAST_SERVICES_FILTER_BY_URL": "servicesFilterByURL",
        "APICAST_SERVICES_LIST": apicast_service_list,
        "APICAST_UPSTREAM_RETRY_CASES": "upstreamRetryCases",
        "APICAST_HTTPS_VERIFY_DEPTH": "httpsVerifyDepth",
        # "APICAST_ACCESS_LOG_FILE": "" Doesnt exists yet!,
        # "THREESCALE_CONFIG_FILE": "" Doesnt exists yet!
        "APICAST_PATH_ROUTING": "pathRoutingEnabled",
        # "APICAST_PATH_ROUTING_ONLY": "" Doesnt exists yet!
        "HTTP_PROXY": "httpProxy",
        "HTTPS_PROXY": "httpsProxy",
        "NO_PROXY": "noProxy",
        "ALL_PROXY": "allProxy",
        "APICAST_LOAD_SERVICES_WHEN_NEEDED": "loadServicesWhenNeeded",
        "APICAST_CACHE_STATUS_CODES": "cacheStatusCodes",
        "APICAST_CACHE_MAX_TIME": "cacheMaxTime",
    }

    REGEX_NAMES: RegexMatcher = {
        re.compile(r"APICAST_SERVICE_(\d+)_CONFIGURATION_VERSION"): set_configuration_version
    }

    def _set(self, apicast, name, value):
        if name in self.NAMES:
            key = self.NAMES[name]
            if callable(key):
                key(apicast, value)
            else:
                apicast[key] = value
            return
        for regex, func in self.REGEX_NAMES.items():
            match = regex.match(name)
            if match:
                func(self.apicast, match, value)
                return
        raise NotImplementedError(f"Env variable {name} doesn't exists or is not yet implemented in operator")

    def _delete(self, apicast, name):
        if name in self.NAMES:
            key = self.NAMES[name]
            if callable(key):
                raise NotImplementedError(f"Callable env variable {name} cannot be deleted yet")
            del apicast[key]
        else:
            raise NotImplementedError(f"Env variable {name} doesn't exists or is not yet implemented in operator")

    def set_many(self, envs: Dict[str, str]):
        def _update(apicast):
            for name, value in envs.items():
                self._set(apicast, name, value)
        self.apicast.modify_and_apply(_update)
        self.wait_function()

    def __getitem__(self, name):
        if name in self.NAMES:
            key = self.NAMES[name]
            if callable(key):
                raise NotImplementedError(f"Callable env variable {name} cannot be read yet")
            return self.apicast[key]
        raise NotImplementedError(f"Env variable {name} doesn't exists or is not yet implemented in operator")

    def __setitem__(self, name, value):
        self.apicast.modify_and_apply(lambda apicast: self._set(apicast, name, value))
        self.wait_function()

    def __delitem__(self, name):
        self.apicast.modify_and_apply(lambda apicast: self._delete(apicast, name))
        self.wait_function()


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with APIcast deployed by operator"""
    CAPABILITIES = {Capability.APICAST, Capability.PRODUCTION_GATEWAY, Capability.CUSTOM_ENVIRONMENT}

    # pylint: disable=too-many-arguments
    def __init__(self, staging: bool, openshift: OpenShiftClient, name, portal_endpoint, generate_name=False) -> None:
        # APIcast operator prepends apicast in front the deployment name
        super().__init__(staging, openshift, name, generate_name)
        self.portal_endpoint = portal_endpoint
        self.apicast = None
        self._environ: OperatorEnviron = None  # type: ignore

    @staticmethod
    def fits():
        return Capability.OCP4 in CapabilityRegistry()

    @property
    def deployment(self):
        return self.openshift.deployment(f"deployment/apicast-{self.name}")

    @property
    def environ(self) -> Properties:
        if self._environ is None:
            self._environ = OperatorEnviron(self.apicast, self.reload)
        return self._environ

    def reload(self):
        self.deployment.rollout()

    def create(self):
        apicast = APIcast.create_instance(
            openshift=self.openshift,
            name=self.name,
            provider_url=self.portal_endpoint
        )
        apicast["logLevel"] = "info"
        apicast["openSSLPeerVerificationEnabled"] = False
        if self.staging:
            apicast["deploymentEnvironment"] = "staging"
            apicast["cacheConfigurationSeconds"] = 0
        else:
            apicast["deploymentEnvironment"] = "production"
            apicast["cacheConfigurationSeconds"] = 300

        self.apicast = apicast.commit()
        # Since apicast operator doesnt have any indication of status of the apicast, we need wait until deployment
        # is created
        time.sleep(2)
        # pylint: disable=protected-access
        self.deployment.wait_for()

    def destroy(self):
        if self.apicast:
            self.apicast.delete(ignore_not_found=True)

    def get_logs(self, since_time=None):
        raise NotImplementedError()

    def set_image(self, image):
        def _update(apicast):
            apicast["image"] = image
        self.apicast.modify_and_apply(_update)
        self.reload()
