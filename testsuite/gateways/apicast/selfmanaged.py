"""Self-managed APIcast already deployed somewhere in OpenShift """
import logging
from typing import Dict, List

from threescale_api.resources import Service

from testsuite import utils
from testsuite.capabilities import Capability
from testsuite.gateways.apicast import AbstractApicast
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.env import Environ
from testsuite.openshift.objects import Routes

LOGGER = logging.getLogger(__name__)


class NoSuitableApicastError(Exception):
    """Raised if no deployment method is found"""


class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed APIcast in OpenShift"""

    CAPABILITIES = {Capability.APICAST,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}
    HAS_PRODUCTION = True

    # pylint: disable=unused-argument
    def __new__(cls, *args, **kwargs):
        if cls is SelfManagedApicast:
            klass = cls.resolve_class()
            super().__new__(klass)
        return super().__new__(cls)

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

    @classmethod
    def resolve_class(cls):
        """Returns actual class that will be instantiated"""
        if cls is SelfManagedApicast:
            for klass in cls.__subclasses__():
                if klass.fits():
                    return klass
            raise NoSuitableApicastError()
        return cls

    @staticmethod
    def fits():   # pylint: disable=unused-argument
        """
        True, if this instance fits the current environment
        Every subclass should override it
        """
        return False

    @property
    def deployment(self):
        """Returns name of the deployment, by default it is just a name"""
        return self.name

    def _routename(self, service):
        """name of route for given service"""
        route = f"{service.entity_id}"
        if self.staging:
            route = f"{route}-stage"
        return route

    @property
    def base_route(self):
        """Route that points at the APIcast itself"""
        if self._base_route is None:
            hostname = self.get_route(f"base-{self.deployment}")
            self._base_route = hostname
        return self._base_route

    def destroy(self):
        super().destroy()

        for route in self._routes:
            if route in self.openshift.routes:
                LOGGER.debug('Removing route "%s"...', route)
                del self.openshift.routes[route]

    def create(self):
        super().create()

        if self.path_routing:
            self.add_route(f"base-{self.deployment}")

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
        result = self.openshift.routes.create(name, kind, service=self.deployment, **{"insecure-policy": "Allow"})
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
    def environ(self) -> Environ:
        return self.openshift.environ(self.deployment)

    def reload(self):
        self.openshift.rollout(f"dc/{self.deployment}")

    def get_logs(self, since_time=None):
        return self.openshift.get_logs(self.deployment, since_time=since_time)
