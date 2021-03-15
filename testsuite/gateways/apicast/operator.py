"""Apicast deployed with ApicastOperator"""
import base64
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import importlib_resources as resources

from threescale_api.resources import Service

from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast, SelfManagedApicastRequirements
from testsuite.capabilities import Capability
from testsuite.openshift.env import Environ
from testsuite.requirements import ThreeScaleAuthDetails
from testsuite.utils import randomize


class OperatorApicastRequirements(SelfManagedApicastRequirements, ABC):
    """Requirements for OperatorApicast"""
    @property
    @abstractmethod
    def auth_details(self) -> ThreeScaleAuthDetails:
        """3scale Auth details"""


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with Apicast deployed by operator"""
    CAPABILITIES = [Capability.APICAST, Capability.PRODUCTION_GATEWAY]

    def __init__(self, requirements: OperatorApicastRequirements) -> None:
        super().__init__(requirements)
        self.auth = requirements.auth_details
        self.deployment = randomize(self.deployment)
        self.name = f"apicast-{self.deployment}"

    def _route_name(self, entity_id):
        if self.staging:
            return f"{entity_id}-staging"
        return f"{entity_id}-production"

    @property
    def _credentials_name(self):
        return f"{self.name}-credentials-secret"

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

    def _create_credentials(self):
        url = self.auth.url.replace('https://', f'https://{self.auth.token}@')
        resource = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": self._credentials_name,
            },
            "data": {
                "AdminPortalURL": base64.b64encode(url.encode("ascii")).decode("ascii"),
            }
        }

        self.openshift.apply(resource)

    def create(self):
        self._create_credentials()

        params = {
            "NAME": self.deployment,
            "CREDENTIALS": self._credentials_name,
        }

        if not self.staging:
            params["CACHE_SECONDS"] = 300
            params["ENVIRONMENT"] = "production"

        path = resources.files('testsuite.resources.apicast_operator').joinpath('apicast.yaml')
        self.openshift.new_app(path, params)

        # Since apicast operator doesnt have any indication of status of the apicast, we need wait until deployment
        # is created
        time.sleep(2)
        # pylint: disable=protected-access
        self.openshift.wait_for_ready(self.name)

    def destroy(self):
        self.openshift.delete("secret", self._credentials_name)
        self.openshift.delete("APIcast", self.deployment)

    def get_logs(self):
        raise NotImplementedError()
