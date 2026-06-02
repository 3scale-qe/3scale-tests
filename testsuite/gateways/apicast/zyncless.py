"""SystemApicast variant for deployments where zync is disabled"""

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from openshift_client import Missing
from threescale_api.resources import Service

from testsuite.gateways.apicast.system import SystemApicast
from testsuite.openshift.objects import Routes

if TYPE_CHECKING:
    from typing import List, Optional

    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class ZyncLessApicast(SystemApicast):
    """SystemApicast for deployments where zync is disabled.

    When zync is disabled, OCP routes for APIcast endpoints are not created automatically.
    This class creates and manages them via lifecycle hooks."""

    def __init__(self, staging: bool, openshift: "Optional[OpenShiftClient]" = None):
        super().__init__(staging, openshift)
        self._routes: "List[str]" = []

    def create(self):
        enabled = self.openshift.api_manager.get_path("spec/zync/enabled")
        if enabled is Missing or enabled:
            raise RuntimeError("ZyncLessApicast requires zync to be disabled in the APIManager spec")

    @staticmethod
    def _route_name(service: Service, production: bool = False) -> str:
        env = "prod" if production else "stage"
        return f"testsuite-{env}-{service.entity_id}"

    def _create_route(self, name: str, endpoint_url: str, ocp_service: str):
        """Creates an OCP route for the given endpoint URL pointing to the given OCP service"""
        assert self.openshift is not None
        hostname = urlparse(endpoint_url).hostname
        if name in self.openshift.routes:
            del self.openshift.routes[name]
        self.openshift.routes.create(
            name, Routes.Types.EDGE, service=ocp_service, hostname=hostname, **{"insecure-policy": "Allow"}
        )
        self._routes.append(name)

    def on_service_create(self, service: Service):
        """Creates staging OCP route"""
        proxy = service.proxy.fetch()
        self._create_route(self._route_name(service), proxy["sandbox_endpoint"], "apicast-staging")

    def on_proxy_promote(self, service: Service):
        """Creates production OCP route"""
        proxy = service.proxy.fetch()
        self._create_route(self._route_name(service, production=True), proxy["endpoint"], "apicast-production")

    def on_service_delete(self, service: Service):
        """Cleans up OCP routes created for this service"""
        if self.openshift is None:
            return
        for name in [self._route_name(service), self._route_name(service, production=True)]:
            if name in self._routes and name in self.openshift.routes:
                del self.openshift.routes[name]
                self._routes.remove(name)
