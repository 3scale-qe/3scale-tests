"""System Apicast that comes deployed with 3scale"""
from typing import TYPE_CHECKING

import backoff

from openshift import OpenShiftPythonException

from testsuite.capabilities import Capability
from testsuite.gateways.apicast import AbstractApicast
from testsuite.openshift.env import Properties
from testsuite.utils import randomize

if TYPE_CHECKING:
    from typing import Optional

    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class SystemApicast(AbstractApicast):
    """Apicast that is deployed with 3scale"""

    CAPABILITIES = {
        Capability.SAME_CLUSTER,
        Capability.CUSTOM_ENVIRONMENT,
        Capability.APICAST,
        Capability.PRODUCTION_GATEWAY,
        Capability.STANDARD_GATEWAY,
        Capability.LOGS,
        Capability.JAEGER,
    }
    HAS_PRODUCTION = True

    def __init__(self, staging: bool, openshift: "Optional[OpenShiftClient]" = None):
        self.staging = staging
        self.openshift: "Optional[OpenShiftClient]" = openshift

    @property
    def deployment(self):
        """Return deployment config name of this apicast"""
        return self.openshift.deployment("dc/apicast-staging" if self.staging else "dc/apicast-production")

    @property
    def environ(self) -> Properties:
        return self.deployment.environ()

    def reload(self):
        self.deployment.rollout()

    def get_logs(self, since_time=None):
        return self.deployment.get_logs(since_time=since_time)

    def disconnect_open_telemetry(self, config_map_name):
        """
        Remove volume attached for jaeger config
        """
        del self.environ["OPENTELEMETRY"]
        del self.environ["OPENTELEMETRY_CONFIG"]
        self.deployment.remove_volume("jaeger-config-vol")
        del self.openshift.config_maps[f"{config_map_name}.ini"]

    def connect_open_telemetry(self, jaeger, open_telemetry_randomized_name=None):
        """
        Modifies the APIcast to send information to jaeger.
        Creates configmap and a volume, mounts the configmap into the volume
        Updates the required env vars
        :param jaeger instance of the Jaeger class carrying the information about the apicast_configuration
        :param open_telemetry_randomized_name: randomized name used for the name of the configmap and for
               the identifying name of the service in jaeger
        """
        if not open_telemetry_randomized_name:
            open_telemetry_randomized_name = randomize("open-telemetry-config")
        config_map_name = f"{open_telemetry_randomized_name}.ini"
        service_name = open_telemetry_randomized_name
        self.openshift.config_maps.add(
            config_map_name, jaeger.apicast_config_open_telemetry(config_map_name, service_name)
        )

        try:
            self.deployment.remove_volume("jaeger-config-vol")
        except OpenShiftPythonException:
            pass
        self.deployment.add_volume("jaeger-config-vol", "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTELEMETRY": "True", "OPENTELEMETRY_CONFIG": f"/tmp/jaeger/{config_map_name}"})
        return service_name

    def _wait_for_apicasts(self):
        """Waits until changes to APIcast have been applied"""
        api_manager = self.openshift.api_manager
        wait_until = backoff.on_predicate(backoff.fibo, max_tries=10)

        # We need to explicitly wait for the deployment being in starting state
        # before waiting for it to be ready, the operator needs time to reconcile
        # its state
        # wait until the Apicast is starting
        wait_until(lambda: not api_manager.ready({"apicast-staging"}))()
        # wait until the Apicast is ready
        wait_until(lambda: api_manager.ready({"apicast-staging", "apicast-production"}))()

    def set_custom_policy(self, policy):
        """Sets custom policy to the Operator"""

        api_manager = self.openshift.api_manager
        api_manager.modify_and_apply(
            lambda manager: manager.set_path("spec/apicast/stagingSpec/customPolicies", [policy])
        )
        self._wait_for_apicasts()

    def remove_custom_policy(self):
        """Removes all custom policies to the Operator"""

        api_manager = self.openshift.api_manager
        api_manager.modify_and_apply(lambda manager: manager.set_path("spec/apicast/stagingSpec/customPolicies", []))
        self._wait_for_apicasts()
