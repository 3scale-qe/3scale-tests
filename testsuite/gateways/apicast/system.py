"""System Apicast that comes deployed with 3scale"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from testsuite.gateways.gateways import AbstractApicast, GatewayRequirements
from testsuite.capabilities import Capability
from testsuite.openshift.env import Environ

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class SystemApicastRequirements(GatewayRequirements, ABC):
    """Requirements for SystemApicast"""
    @property
    @abstractmethod
    def staging_deployment(self) -> str:
        """Returns staging deployment"""

    @property
    @abstractmethod
    def production_deployment(self) -> str:
        """Returns production deployment"""


class SystemApicast(AbstractApicast):
    """Apicast that is deployed with 3scale"""

    CAPABILITIES = {Capability.SAME_CLUSTER,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.APICAST,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.STANDARD_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}

    def __init__(self, requirements: SystemApicastRequirements):
        if requirements.staging:
            self.deployment = requirements.staging_deployment
        else:
            self.deployment = requirements.production_deployment
        self.openshift: "OpenShiftClient" = requirements.current_openshift
        self.name = self.deployment
        self.options = requirements

    @property
    def environ(self) -> Environ:
        return self.openshift.environ(self.deployment)

    def reload(self):
        self.openshift.rollout(f"dc/{self.deployment}")

    def get_logs(self, since_time=None):
        return self.openshift.get_logs(self.deployment, since_time=since_time)

    def connect_jaeger(self, jaeger, jaeger_randomized_name):
        """
        Modifies the apicast to send information to jaeger.
        Creates configmap and a volume, mounts the configmap into the volume
        Updates the required env vars
        :param jaeger instance of the Jaeger class carrying the information about the apicast_configuration
        :param jaeger_randomized_name: randomized name used for the name of the configmap and for
               the identifying name of the service in jaeger
        """
        config_map_name = f"{jaeger_randomized_name}.json"
        service_name = jaeger_randomized_name
        self.openshift.config_maps.add(config_map_name, jaeger.apicast_config(config_map_name, service_name))
        self.openshift.add_volume(self.deployment, "jaeger-config-vol",
                                  "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTRACING_TRACER": "jaeger",
                               "OPENTRACING_CONFIG": f"/tmp/jaeger/{config_map_name}"})
