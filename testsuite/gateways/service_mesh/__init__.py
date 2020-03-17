"""Service mesh gateway"""
from abc import ABC, abstractmethod

from threescale_api.resources import Service, Application

from testsuite.gateways.gateways import AbstractGateway, GatewayRequirements, Capability
from testsuite.gateways.service_mesh.client import ServiceMeshHttpClient
from testsuite.gateways.service_mesh.objects import ServiceMesh, Httpbin


class ServiceMeshRequirements(GatewayRequirements, ABC):
    """Requirements for ServiceMeshGateway"""

    @property
    @abstractmethod
    def httpbin(self) -> Httpbin:
        """Returns configured httpbin object"""

    @property
    @abstractmethod
    def mesh(self) -> ServiceMesh:
        """Returns configured service mesh object"""


class ServiceMeshGateway(AbstractGateway):
    """Gateway for Service mesh configured with 3scale through 3scale-istio-adapter"""

    CAPABILITIES = [Capability.SERVICE_MESH]

    def __init__(self, configuration: ServiceMeshRequirements):
        self.mesh = configuration.mesh
        self.httpbin = configuration.httpbin
        self._ingress_url = None

    def before_service(self, service_params: dict) -> dict:
        service_params['deployment_option'] = "service_mesh_istio"
        return service_params

    def on_service_create(self, service: Service):
        self.httpbin.patch_service(service["id"])

    def on_application_create(self, application: Application):
        # pylint: disable=protected-access
        application._client_factory = self._create_api_client

    def create(self):
        self.mesh.patch_credentials()

    def destroy(self):
        return

    # pylint: disable=unused-argument
    def _create_api_client(self, application, endpoint, session, verify):
        return ServiceMeshHttpClient(app=application,
                                     session=session,
                                     verify=verify,
                                     openshift=self.mesh.openshift,
                                     root_path=self.httpbin.path,
                                     root_url=self.mesh.ingress_url)
