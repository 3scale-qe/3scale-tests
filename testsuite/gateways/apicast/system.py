"""System Apicast that comes deployed with 3scale"""
from typing import TYPE_CHECKING

from testsuite.capabilities import Capability
from testsuite.gateways.apicast import AbstractApicast
from testsuite.openshift.env import Environ

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class SystemApicast(AbstractApicast):
    """Apicast that is deployed with 3scale"""

    CAPABILITIES = {Capability.SAME_CLUSTER,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.APICAST,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.STANDARD_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}
    HAS_PRODUCTION = True

    def __init__(self, staging, openshift):
        self.staging = staging
        self.deployment = "apicast-staging" if staging else "apicast-production"
        self.openshift: "OpenShiftClient" = openshift
        self.name = self.deployment

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
