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

    def before_service(self, service_params: Dict) -> Dict:
        service_params.update({
            "deployment_option": "self_managed"
        })
        return service_params

    def before_proxy(self, service: Service, proxy_params: Dict) -> Dict:
        name = service.entity_id
        proxy_params.update({
            "sandbox_endpoint": self.staging_endpoint % name,
            "endpoint": self.production_endpoint % name
        })
        return proxy_params

    def reload(self):
        raise NotImplementedError()
