"""SelfManaged Apicast"""
from abc import ABC, abstractmethod
from typing import Dict

from threescale_api.resources import Service

from testsuite.gateways.gateways import AbstractApicast, GatewayRequirements
from testsuite.capabilities import Capability
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.env import Environ


class SelfManagedApicastRequirements(GatewayRequirements, ABC):
    """Requirements for SelfManagedApicast"""
    @property
    @abstractmethod
    def staging_endpoint(self) -> str:
        """Returns staging endpoint"""

    @property
    @abstractmethod
    def production_endpoint(self) -> str:
        """Returns production endpoint"""

    @property
    @abstractmethod
    def staging_deployment(self) -> str:
        """Returns staging deployment"""

    @property
    @abstractmethod
    def production_deployment(self) -> str:
        """Returns production deployment"""


class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed Apicast in OpenShift"""

    CAPABILITIES = {Capability.APICAST,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}

    def __init__(self, requirements: SelfManagedApicastRequirements) -> None:
        self.staging = requirements.staging
        if self.staging:
            self.deployment = requirements.staging_deployment
            self.endpoint = requirements.staging_endpoint
        else:
            self.deployment = requirements.production_deployment
            self.endpoint = requirements.production_endpoint
        # Load openshift configuration
        self.openshift: OpenShiftClient = requirements.current_openshift
        self.options = requirements

    def before_service(self, service_params: Dict) -> Dict:
        service_params.update({
            "deployment_option": "self_managed"
        })
        return service_params

    def before_proxy(self, service: Service, proxy_params: Dict) -> Dict:
        entity_id = service.entity_id
        key = "sandbox_endpoint" if self.staging else "endpoint"
        proxy_params.update({
            key: self.endpoint % entity_id
        })
        return proxy_params

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
        service_name = jaeger_randomized_name
        config_map_name = f"{jaeger_randomized_name}.json"
        self.openshift.config_maps.add(config_map_name, jaeger.apicast_config(config_map_name, service_name))
        self.openshift.add_volume(self.deployment, "jaeger-config-vol",
                                  "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTRACING_TRACER": "jaeger",
                               "OPENTRACING_CONFIG": f"/tmp/jaeger/{config_map_name}"})

    def update_image_stream(self, image_stream: str, amp_release: str = "latest"):
        """
        Updates the image stream the deployment is using
        :param image_stream: name of the image stream
        :param amp_release: tag of the image stream
        """
        self.openshift.patch("dc", self.deployment, {"spec": {
            "triggers": [{
                "imageChangeParams": {
                    "automatic": True,
                    "containerNames": [
                        self.deployment],
                    "from":{
                        "name": f"{image_stream}:{amp_release}"}},
                    "type": "ImageChange"},
                {"type": "ConfigChange"}]}})
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.deployment)
