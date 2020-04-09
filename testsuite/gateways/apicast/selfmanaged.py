"""SelfManaged Apicast"""
from abc import ABC, abstractmethod
from typing import Dict
from threescale_api.resources import Service

from testsuite.gateways.gateways import AbstractApicast, Capability, GatewayRequirements


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
    """Gateway for use with already deployed self-managed Apicast without ability to edit it"""

    CAPABILITIES = [Capability.APICAST]

    def __init__(self, requirements: SelfManagedApicastRequirements) -> None:
        self.staging_endpoint = requirements.staging_endpoint
        self.production_endpoint = requirements.production_endpoint

        if requirements.staging:
            self.deployment = requirements.staging_deployment
        else:
            self.deployment = requirements.production_deployment

        # Load openshift configuration
        self.openshift = requirements.current_openshift

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
