"""Apicast deployed with ApicastOperator"""
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from threescale_api.resources import Service

from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast, SelfManagedApicastRequirements


class OperatorApicastRequirements(SelfManagedApicastRequirements, ABC):
    """Requirements for OperatorApicast"""
    @property
    @abstractmethod
    def staging_service(self):
        """Service for staging apicast, needed for route creation"""

    @property
    @abstractmethod
    def production_service(self):
        """Service for production apicast, needed for route creation"""


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with Apicast deployed by operator"""
    def __init__(self, requirements: OperatorApicastRequirements) -> None:
        super().__init__(requirements)
        self.service_staging = requirements.staging_service
        self.service_production = requirements.production_service

    def register_service(self, service: Service):
        entity_id = service.entity_id
        staging_url = urlparse(self.staging_endpoint % entity_id)
        prod_url = urlparse(self.production_endpoint % entity_id)
        self.openshift.routes.create(name=f"{entity_id}-staging",
                                     service=self.service_staging, hostname=staging_url.hostname)
        self.openshift.routes.create(name=f"{entity_id}-production",
                                     service=self.service_production, hostname=prod_url.hostname)

    def unregister_service(self, service: Service):
        del self.openshift.routes[f"{service.entity_id}-staging"]
        del self.openshift.routes[f"{service.entity_id}-production"]

    def set_env(self, name: str, value):
        raise NotImplementedError()

    def get_env(self, name: str):
        raise NotImplementedError()

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.deployment}"])
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(f"deployment/{self.deployment}")
