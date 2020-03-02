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

    def __init__(self, staging: bool, configuration, openshift: OpenShiftClient) -> None:
        """
        :param staging_endpoint: Staging endpoint URL template with with one parameter to insert the service name
            e.g http://%s-staging.localhost:8080
        :param production_endpoint: Production endpoint URL template with with one parameter to insert the service name
            e.g http://%s-production.localhost:8080
        """
        super().__init__(staging, configuration, openshift)
        self.staging_endpoint = configuration["sandbox_endpoint"]
        self.production_endpoint = configuration["production_endpoint"]

    def get_service_settings(self, service_settings: Dict) -> Dict:
        service_settings.update({
            "deployment_option": "self_managed"
        })
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        name = service["system_name"]
        proxy_settings.update({
            "sandbox_endpoint": self.staging_endpoint % name,
            "endpoint": self.production_endpoint % name
        })
        return proxy_settings

    def set_env(self, name: str, value):
        raise NotImplementedError()

    def get_env(self, name: str):
        raise NotImplementedError()

    def reload(self):
        raise NotImplementedError()
