"""Apicast deployed with ApicastOperator"""
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from threescale_api.resources import Service

from testsuite.capabilities import Capability
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast, SelfManagedApicastRequirements
from testsuite.openshift.crd.apicast import APIcast
from testsuite.openshift.env import Environ
from testsuite.requirements import ThreeScaleAuthDetails


class OperatorApicastRequirements(SelfManagedApicastRequirements, ABC):
    """Requirements for OperatorApicast"""
    @property
    @abstractmethod
    def auth_details(self) -> ThreeScaleAuthDetails:
        """3scale Auth details"""


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with Apicast deployed by operator"""
    CAPABILITIES = {Capability.APICAST, Capability.PRODUCTION_GATEWAY}

    def __init__(self, requirements: OperatorApicastRequirements) -> None:
        super().__init__(requirements)
        self.auth = requirements.auth_details
        self.name = f"apicast-{self.deployment}"
        self.apicast = None

    def _route_name(self, entity_id):
        if self.staging:
            return f"{entity_id}-staging"
        return f"{entity_id}-production"

    @property
    def environ(self) -> Environ:
        raise NotImplementedError("Operator doesn't support environment")

    def on_service_create(self, service: Service):
        super().on_service_create(service)
        entity_id = service.entity_id
        url = urlparse(self.endpoint % entity_id)
        name = self._route_name(entity_id)
        self.openshift.routes.create(name=name,
                                     service=self.name, hostname=url.hostname)

    def on_service_delete(self, service: Service):
        super().on_service_delete(service)
        del self.openshift.routes[self._route_name(service.entity_id)]

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.name}"])
        # pylint: disable=protected-access
        self.openshift.wait_for_ready(self.name)

    def create(self):
        provider_url = self.auth.url.replace('https://', f'https://{self.auth.token}@')

        apicast = APIcast.create_instance(
            openshift=self.openshift,
            name=self.deployment,
            provider_url=provider_url
        )
        apicast["logLevel"] = "info"
        apicast["openSSLPeerVerificationEnabled"] = False
        if self.staging:
            apicast["deploymentEnvironment"] = "staging"
            apicast["cacheConfigurationSeconds"] = 0
        else:
            apicast["deploymentEnvironment"] = "production"
            apicast["cacheConfigurationSeconds"] = 300

        self.apicast = apicast.commit()
        # Since apicast operator doesnt have any indication of status of the apicast, we need wait until deployment
        # is created
        time.sleep(2)
        # pylint: disable=protected-access
        self.openshift.wait_for_ready(self.name)

    def destroy(self):
        if self.apicast:
            self.apicast.delete(ignore_not_found=True)

    def get_logs(self, since_time=None):
        raise NotImplementedError()
