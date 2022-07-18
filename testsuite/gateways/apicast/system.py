"""System Apicast that comes deployed with 3scale"""
from typing import TYPE_CHECKING

from testsuite.capabilities import Capability
from testsuite.gateways.apicast import AbstractApicast
from testsuite.openshift.env import Properties

if TYPE_CHECKING:
    from typing import Optional
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
        self.deployment.add_volume("jaeger-config-vol",
                                   "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTRACING_TRACER": "jaeger",
                               "OPENTRACING_CONFIG": f"/tmp/jaeger/{config_map_name}"})
