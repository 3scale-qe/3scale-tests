"""Module containing all APIcast gateways"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from openshift_client import OpenShiftPythonException
from threescale_api.resources import Service

from testsuite import utils
from testsuite.capabilities import Capability
from testsuite.gateways import AbstractGateway
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.deployments import Deployment
from testsuite.openshift.env import Properties
from testsuite.openshift.objects import Routes

LOGGER = logging.getLogger(__name__)


class AbstractApicast(AbstractGateway, ABC):
    """Interface defining basic functionality of an APIcast gateway"""

    CAPABILITIES = {Capability.APICAST}

    @abstractmethod
    def reload(self):
        """Reloads gateway"""

    @abstractmethod
    def get_logs(self, since_time: Optional[datetime] = None) -> str:
        """Gets the logs of the active Apicast pod from specific time"""

    def create(self):
        pass

    def destroy(self):
        pass


# pylint: disable=too-many-instance-attributes
class OpenshiftApicast(AbstractApicast, ABC):
    """Super-class for selfmanaged apicast deployed to openshift"""

    CAPABILITIES = {
        Capability.APICAST,
        Capability.CUSTOM_ENVIRONMENT,
        Capability.PRODUCTION_GATEWAY,
        Capability.LOGS,
        Capability.JAEGER,
    }
    HAS_PRODUCTION = True
    PRIORITY = 100

    # pylint: disable=too-many-arguments
    def __init__(self, staging: bool, openshift: OpenShiftClient, name, generate_name=False, path_routing=False):
        self.staging = staging
        self.secure = True
        self.path_routing = path_routing

        self.openshift = openshift
        self.name = name
        if generate_name:
            name = f"{name}-stage" if staging else name
            self.name = f"{name}-{utils.randomize(utils._whoami()[:8])}"
        self._routes: List[str] = []
        self._base_route = None
        self._to_delete: List[Tuple[str, str]] = []

    @staticmethod
    def fits(openshift: OpenShiftClient):  # pylint: disable=unused-argument
        """
        True, if this instance fits the current environment
        Every subclass should override it
        """
        return False

    @abstractmethod
    def setup_tls(self, secret_name, https_port):
        """Sets up TLS with the current gateway"""

    @property
    def deployment(self) -> Deployment:
        """Gateway deployment"""
        # dc are replaced with deployments in 2.15-dev
        try:
            self.openshift.do_action("get", [f"deployment/{self.name}"])
            return self.openshift.deployment(f"deployment/{self.name}")
        except OpenShiftPythonException:
            return self.openshift.deployment(f"dc/{self.name}")

    def _routename(self, service):
        """name of route for given service"""
        route = f"{service.entity_id}-{self.name}"
        return route

    @property
    def base_route(self):
        """Route that points at the APIcast itself"""
        if self._base_route is None:
            hostname = self.get_route(f"base-{self.deployment.name}")
            self._base_route = hostname
        return self._base_route

    def destroy(self):
        super().destroy()

        for route in self._routes:
            if route in self.openshift.routes:
                LOGGER.debug('Removing route "%s"...', route)
                del self.openshift.routes[route]

        for kind, name in self._to_delete:
            self.openshift.delete(kind, name, ignore_not_found=True)

    def create(self):
        super().create()

        if self.path_routing:
            self.add_route(f"base-{self.deployment.name}")

    def before_service(self, service_params: Dict) -> Dict:
        service_params.update({"deployment_option": "self_managed"})
        return service_params

    def before_proxy(self, service: Service, proxy_params: Dict) -> Dict:
        if self.path_routing:
            host = self.base_route
        else:
            route = self.add_route(self._routename(service))
            host = route.model.spec.host

        key = "sandbox_endpoint" if self.staging else "endpoint"
        url = f"https://{host}" if self.secure else f"http://{host}"
        proxy_params.update({key: url})
        return proxy_params

    def on_service_delete(self, service: Service):
        super().on_service_delete(service)
        if not self.path_routing:
            self.delete_route(self._routename(service))

    def add_route(self, name, kind=Routes.Types.EDGE):
        """Adds new route for this APIcast"""
        result = self.openshift.routes.create(name, kind, service=self.deployment.name, **{"insecure-policy": "Allow"})
        self._routes.append(name)
        return result

    def get_route(self, name):
        """Return route host with specified name"""
        return self.openshift.do_action("get", ["route", name, "-o", "jsonpath={$..spec..host}"]).out().strip()

    def delete_route(self, name):
        """Delete route"""
        if name in self._routes and name in self.openshift.routes:
            del self.openshift.routes[name]
            self._routes.remove(name)

    @property
    def environ(self) -> Properties:
        return self.deployment.environ()

    def reload(self):
        self.deployment.rollout()

    def get_logs(self, since_time=None):
        return self.deployment.get_logs(since_time=since_time)

    def set_image(self, image):
        """Sets specific image to the deployment config and redeploys it"""
        self.deployment.patch(
            [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": image}], patch_type="json"
        )
        # pylint: disable=protected-access
        self.deployment.wait_for()
