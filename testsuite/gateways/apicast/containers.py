"""Collection of gateways that run in containerized environment"""
from typing import Dict

from threescale_api.resources import Service

from testsuite.gateways.apicast.selfmanaged import SelfManagedApicastRequirements
from testsuite.gateways.gateways import AbstractApicast


class ContainerizedApicast(AbstractApicast):
    """
    Gateway intended for use with RHEL based Apicasts deployed in containerized environments
    For the time being it has same requirements as SelfManagedApicast
    """
    def __init__(self, requirements: SelfManagedApicastRequirements) -> None:
        self.staging_endpoint = requirements.staging_endpoint
        self.production_endpoint = requirements.production_endpoint

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
