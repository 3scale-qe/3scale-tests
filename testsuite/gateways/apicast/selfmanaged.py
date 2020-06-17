"""SelfManaged Apicast"""
from abc import ABC, abstractmethod
from typing import Dict
from threescale_api.resources import Service

from testsuite.gateways.gateways import AbstractApicast, Capability, GatewayRequirements
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
    """Gateway for use with already deployed self-managed Apicast without ability to edit it"""

    CAPABILITIES = [Capability.APICAST, Capability.CUSTOM_ENVIRONMENT]

    def __init__(self, requirements: SelfManagedApicastRequirements) -> None:
        # self.staging_endpoint = requirements.staging_endpoint
        # self.production_endpoint = requirements.production_endpoint
        self.staging = requirements.staging
        if self.staging:
            self.deployment = requirements.staging_deployment
            self.endpoint = requirements.staging_endpoint
        else:
            self.deployment = requirements.production_deployment
            self.endpoint = requirements.production_endpoint
        # Load openshift configuration
        self.openshift = requirements.current_openshift

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
        self.openshift.rollout(self.deployment)
