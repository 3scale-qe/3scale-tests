"""System Apicast that comes deployed with 3scale"""

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import backoff
from openshift_client import Missing, OpenShiftPythonException
from threescale_api.resources import Service

from testsuite.capabilities import Capability
from testsuite.gateways.apicast import AbstractApicast
from testsuite.openshift.env import Properties
from testsuite.openshift.objects import Routes
from testsuite.utils import randomize

if TYPE_CHECKING:
    from typing import List, Optional

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
        self._routes: "List[str]" = []

    @property
    def _zync_disabled(self) -> bool:
        """Returns True if zync is disabled in the APIManager spec"""
        if self.openshift is None:
            return False
        enabled = self.openshift.api_manager.get_path("spec/zync/enabled")
        return enabled is not Missing and not enabled

    @staticmethod
    def _route_name(service: Service, production: bool = False) -> str:
        env = "prod" if production else "stage"
        return f"testsuite-{env}-{service.entity_id}"

    def _create_route(self, name: str, endpoint_url: str, ocp_service: str):
        """Creates an OCP route for the given endpoint URL pointing to the given OCP service"""
        assert self.openshift is not None
        hostname = urlparse(endpoint_url).hostname
        if name in self.openshift.routes:
            del self.openshift.routes[name]
        self.openshift.routes.create(
            name, Routes.Types.EDGE, service=ocp_service, hostname=hostname, **{"insecure-policy": "Allow"}
        )
        self._routes.append(name)

    def on_service_create(self, service: Service):
        """Creates staging OCP route when zync is disabled"""
        if not self._zync_disabled:
            return
        proxy = service.proxy.fetch()
        self._create_route(self._route_name(service), proxy["sandbox_endpoint"], "apicast-staging")

    def on_proxy_promote(self, service: Service):
        """Creates production OCP route when zync is disabled"""
        if not self._zync_disabled:
            return
        proxy = service.proxy.fetch()
        self._create_route(self._route_name(service, production=True), proxy["endpoint"], "apicast-production")

    def on_service_delete(self, service: Service):
        """Cleans up OCP routes created for this service"""
        if self.openshift is None:
            return
        for name in [self._route_name(service), self._route_name(service, production=True)]:
            if name in self._routes and name in self.openshift.routes:
                del self.openshift.routes[name]
                self._routes.remove(name)

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
