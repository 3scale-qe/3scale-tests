"""Apicast deployed with ApicastOperator"""

import re
import time
from typing import Dict, Callable, Pattern, Any, Match, Union

from weakget import weakget

from testsuite import settings
from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.crd.apicast import APIcast
from testsuite.openshift.env import Properties

from . import OpenshiftApicast

StrMatcher = Dict[str, Union[str, Callable[[APIcast, Any], Any]]]
RegexMatcher = Dict[Pattern, Callable[[APIcast, Match, Any], Any]]


def apicast_service_list(apicast: APIcast, services: str):
    """Sets APICAST_SERVICE_LIST in the APIcast CR"""
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
        "APICAST_CONFIGURATION_LOADER": "configurationLoadMode",
        "APICAST_CONFIGURATION_CACHE": "cacheConfigurationSeconds",
        "APICAST_LOG_LEVEL": "logLevel",
    }

    REGEX_NAMES: RegexMatcher = {re.compile(r"APICAST_SERVICE_(\d+)_CONFIGURATION_VERSION"): set_configuration_version}

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


class OperatorApicast(OpenshiftApicast):
    """Gateway for use with APIcast deployed by operator"""

    CAPABILITIES = {
        Capability.APICAST,
        Capability.PRODUCTION_GATEWAY,
        Capability.CUSTOM_ENVIRONMENT,
        Capability.LOGS,
        Capability.JAEGER,
    }
    PRIORITY = 1000

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        staging: bool,
        openshift: OpenShiftClient,
        name,
        portal_endpoint,
        image=None,
        generate_name=False,
        path_routing=False,
    ):
        # APIcast operator prepends apicast in front the deployment name
        super().__init__(staging, openshift, name, generate_name, path_routing)
        self.portal_endpoint = portal_endpoint
        self.apicast = None
        self.image = image
        self._environ: OperatorEnviron = None  # type: ignore

    @staticmethod
    def fits(openshift: OpenShiftClient):
        return (
            Capability.OCP4 in CapabilityRegistry()
            and openshift.project_exists
            and weakget(settings)["operators"]["apicast"]["openshift"] % False
        )

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
        # Create secret with Provider URL credentials
        self.openshift.secrets.create(self.name, string_data={"AdminPortalURL": self.portal_endpoint})
        self._to_delete.append(("secret", self.name))

        apicast = APIcast.create_instance(
            openshift=self.openshift,
            name=self.name,
        )
        apicast["logLevel"] = "info"
        apicast["openSSLPeerVerificationEnabled"] = False
        if self.staging:
            apicast["deploymentEnvironment"] = "staging"
            apicast["cacheConfigurationSeconds"] = 0
            apicast["configurationLoadMode"] = "lazy"
        else:
            apicast["deploymentEnvironment"] = "production"
            apicast["cacheConfigurationSeconds"] = 300
        if self.image:
            apicast["image"] = self.image
        self.apicast = apicast.commit()
        # Since apicast operator doesnt have any indication of status of the apicast, we need wait until deployment
        # is created
        time.sleep(2)
        # pylint: disable=protected-access
        self.deployment.wait_for()

        super().create()

    def destroy(self):
        if self.apicast:
            self.apicast.delete(ignore_not_found=True)

        super().destroy()

    def setup_tls(self, secret_name, https_port):
        def _add_tls(apicast):
            apicast["httpsPort"] = https_port
            apicast["httpsCertificateSecretRef"] = {"name": secret_name}

        self.apicast.modify_and_apply(_add_tls)
        self.reload()

    def get_logs(self, since_time=None):
        return self.deployment.get_logs(since_time=since_time)

    def set_image(self, image):
        def _update(apicast):
            apicast["image"] = image

        self.apicast.modify_and_apply(_update)
        self.reload()

    def disconnect_open_telemetry(self, *args):
        """
        Current tests delete apicast after opentelemetry tests, cleanup of the
        apicast itself will clean all configuration for opentelemetry as well
        """

    def connect_open_telemetry(self, jaeger):
        """
        Modifies the APIcast to send information to jaeger.
        Creates configmap and a volume, mounts the configmap into the volume
        Updates the required env vars
        :param jaeger instance of the Jaeger class carrying the information about the apicast_configuration
        :returns Name of the jaeger service
        """
        secret_name = f"{self.name}-jaeger"
        self.openshift.secrets.create(
            name=secret_name, string_data=jaeger.apicast_config_open_telemetry("config", self.name)
        )
        self._to_delete.append(("secret", secret_name))

        def _add_open_telemetry(apicast):
            apicast["openTelemetry"] = {
                "enabled": True,
                "tracingConfigSecretRef": {"name": secret_name},
            }

        self.apicast.modify_and_apply(_add_open_telemetry)
        self.reload()
        return self.name

    def __getstate__(self):
        """
        Custom serializer for pickle module
        more info here: https://docs.python.org/3/library/pickle.html#object.__getstate__
        """
        return {
            "reload": self.reload,
            "name": self.name,
            "openshift": self.openshift,
        }

    def __setstate__(self, state):
        """
        Custom deserializer for pickle module
        more info here: https://docs.python.org/3/library/pickle.html#object.__setstate__
        """
        self.openshift = state["openshift"]
        result = self.openshift.do_action("get", ["apicast", state["name"], "-o", "yaml"])
        self.apicast = APIcast(string_to_model=result.out())
        self.name = state["name"]
        self._environ = OperatorEnviron(self.apicast, state["reload"])

    def set_custom_policy(self, policy):
        """Sets custom policy to the Operator"""
        self.apicast.modify_and_apply(
            lambda apicast: apicast.model.spec.setdefault("customPolicies", []).append(policy)
        )
        self.reload()

    def remove_custom_policy(self):
        """Removes all custom policies to the Operator"""
        self.apicast.modify_and_apply(lambda apicast: apicast.model.spec.setdefault("customPolicies", []).clear())
        self.reload()
