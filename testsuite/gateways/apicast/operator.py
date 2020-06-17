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
        if requirements.staging:
            self.service = requirements.staging_service
        else:
            self.service = requirements.production_service

    def _route_name(self, entity_id):
        if self.staging:
            return f"{entity_id}-staging"
        return f"{entity_id}-production"

    def on_service_create(self, service: Service):
        entity_id = service.entity_id
        url = urlparse(self.endpoint % entity_id)
        name = self._route_name(entity_id)
        self.openshift.routes.create(name=name,
                                     service=self.service, hostname=url.hostname)

    def on_service_delete(self, service: Service):
        del self.openshift.routes[self._route_name(service.entity_id)]

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.deployment}"])
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(f"deployment/{self.deployment}")
