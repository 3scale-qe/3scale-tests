"""System Apicast that comes deployed with 3scale"""

from typing import TYPE_CHECKING

import backoff

from openshift_client import OpenShiftPythonException

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
        # dc are replaced with deployments in 2.15-dev
        name = "apicast-staging" if self.staging else "apicast-production"
        try:
            self.openshift.do_action("get", [f"deployment/{name}"])
            return self.openshift.deployment(f"deployment/{name}")
        except OpenShiftPythonException:
            return self.openshift.deployment(f"dc/{name}")

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
        self.openshift.api_manager.modify_and_apply(
            lambda manager: manager.set_path("spec/apicast/stagingSpec/openTelemetry", {})
        )

        del self.openshift.secrets[f"{config_map_name}.ini"]

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

        self.openshift.secrets.create(
            name=config_map_name, string_data=jaeger.apicast_config_open_telemetry(config_map_name, service_name)
        )

        def _add_open_telemetry(manager):
            manager.set_path(
                "spec/apicast/stagingSpec/openTelemetry",
                {
                    "enabled": True,
                    "tracingConfigSecretRef": {"name": config_map_name},
                },
            )

        self.openshift.api_manager.modify_and_apply(_add_open_telemetry)

        self._wait_for_apicasts()

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
