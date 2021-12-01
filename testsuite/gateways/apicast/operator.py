"""Apicast deployed with ApicastOperator"""
import time
from typing import Dict

from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.crd.apicast import APIcast
from testsuite.openshift.env import Properties

from .selfmanaged import SelfManagedApicast


def apicast_service_list(apicast: APIcast, services: str):
    """Sets APICAST_SERVICE_LIST in the APIcast CR """
    service_list = str(services).split(",")
    apicast["enabledServices"] = service_list


class OperatorEnviron(Properties):
    """
    Implements Properties for use in Operator and
    transforms APIcast environmental variables into operator properties
    """
    def __init__(self, apicast: APIcast, wait_function) -> None:
        self.apicast = apicast
        self.wait_function = wait_function

    NAMES = {
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
        # "APICAST_SERVICE_{service.entity_id}_CONFIGURATION_VERSION": ""  # TODO: Works differently
    }

    def _set(self, name, value, commit=True):
        if name in self.NAMES:
            key = self.NAMES[name]
            if callable(key):
                key(self.apicast, value)
            else:
                self.apicast[key] = value
            if commit:
                self.apicast.apply()
                self.wait_function()
        else:
            raise NotImplementedError(f"Env variable {name} doesn't exists or is not yet implemented in operator")

    def set_many(self, envs: Dict[str, str]):
        for name, value in envs.items():
            self._set(name, value, commit=False)
        self.apicast.apply()
        self.wait_function()

    def __getitem__(self, name):
        if name in self.NAMES:
            key = self.NAMES[name]
            if callable(key):
                raise NotImplementedError(f"Callable env variable {name} cannot be read yet")
            return self.apicast[key]
        raise NotImplementedError(f"Env variable {name} doesn't exists or is not yet implemented in operator")

    def __setitem__(self, name, value):
        self._set(name, value)

    def __delitem__(self, name):
        if name in self.NAMES:
            key = self.NAMES[name]
            if callable(key):
                raise NotImplementedError(f"Callable env variable {name} cannot be deleted yet")
            del self.apicast[key]
            self.apicast.apply()
            self.wait_function()
        else:
            raise NotImplementedError(f"Env variable {name} doesn't exists or is not yet implemented in operator")


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
        return f"apicast-{super().deployment}"

    @property
    def environ(self) -> Properties:
        if self._environ is None:
            self._environ = OperatorEnviron(self.apicast, self.reload)
        return self._environ

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.deployment}"])
        # pylint: disable=protected-access
        self.openshift.wait_for_ready(self.deployment)

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
        self.openshift.wait_for_ready(self.deployment)

    def destroy(self):
        if self.apicast:
            self.apicast.delete(ignore_not_found=True)

    def get_logs(self, since_time=None):
        raise NotImplementedError()
