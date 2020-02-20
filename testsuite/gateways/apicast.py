"""Collection of gateways that are Apicast-based"""
from typing import Dict

from threescale_api.resources import Service

from testsuite.gateways.gateways import AbstractApicast, Capability
from testsuite.openshift.client import OpenShiftClient


class SystemApicast(AbstractApicast):
    """Apicast that is deployed with 3scale"""

    CAPABILITIES = [Capability.SAME_CLUSTER,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.APICAST,
                    Capability.PRODUCTION_GATEWAY]

    def __init__(self, staging: bool, configuration, openshift):
        super().__init__(staging, configuration, openshift)
        if staging:
            self.deployment_name = configuration["staging_deployment"]
        else:
            self.deployment_name = configuration["production_deployment"]
        self.openshift: OpenShiftClient = openshift()

    def get_service_settings(self, service_settings: Dict) -> Dict:
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        return proxy_settings

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment_name)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment_name)[name]

    def reload(self):
        self.openshift.rollout(f"dc/{self.deployment_name}")


class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed Apicast without ability to edit it"""

    CAPABILITIES = [Capability.APICAST]

    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)
        self.staging_endpoint = configuration["sandbox_endpoint"]
        self.production_endpoint = configuration["production_endpoint"]

        deployments = configuration["deployments"]
        if staging:
            self.deployment = deployments["staging"]
        else:
            self.deployment = deployments["production"]

        # Load openshift configuration
        self.project = configuration.get("project", "threescale")
        self.server = configuration.get("server", "default")
        self.openshift = openshift(server_name=self.server, project_name=self.project)

    def get_service_settings(self, service_settings: Dict) -> Dict:
        service_settings.update({
            "deployment_option": "self_managed"
        })
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        entity_id = service.entity_id
        proxy_settings.update({
            "sandbox_endpoint": self.staging_endpoint % entity_id,
            "endpoint": self.production_endpoint % entity_id
        })
        return proxy_settings

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment)[name]

    def reload(self):
        self.openshift.rollout(self.deployment)
