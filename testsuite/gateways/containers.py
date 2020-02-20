"""Collection of gateways that run in containerized environment"""
from typing import Dict

from testsuite.gateways.gateways import AbstractApicast


class ContainerizedApicast(AbstractApicast):
    """
    Gateway intended for use with RHEL based Apicasts deployed in containerized environments
    For the time being its is functionally the same as SelfManagedApicast
    """
    def __init__(self, staging: bool, configuration, openshift) -> None:
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
