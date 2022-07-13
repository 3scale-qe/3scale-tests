"""Service mesh gateway"""
from typing import Dict

from threescale_api.resources import Service, Application

from testsuite.capabilities import Capability
from testsuite.gateways.gateways import AbstractGateway
from testsuite.gateways.service_mesh.client import ServiceMeshHttpClient
from testsuite.gateways.service_mesh.httpbin import Httpbin
from testsuite.gateways.service_mesh.mesh import ServiceMesh
from testsuite.utils import generate_tail


# pylint: disable=too-many-instance-attributes,protected-access
class ServiceMeshGateway(AbstractGateway):
    """Gateway for Service mesh configured with 3scale through 3scale-istio-adapter"""

    CAPABILITIES = {Capability.SERVICE_MESH}

    def __init__(self, openshift, httpbin, mesh, portal_endpoint):
        self.env_vars: Dict[str, str] = {}
        self.identifier = generate_tail()
        self.openshift = openshift
        self.httpbin_oc = httpbin
        self.mesh_oc = mesh
        self.portal_endpoint = portal_endpoint

        # Disable mypy for this one line, because it just cannot understand that the httpbin
        # will have value at the time of anyone using it
        self.httpbin: Httpbin = None       # type: ignore
        self.mesh: ServiceMesh = None      # type: ignore

    def before_service(self, service_params: dict) -> dict:
        service_params['deployment_option'] = "service_mesh_istio"
        return service_params

    def on_service_create(self, service: Service):
        self.httpbin.patch_service(service["id"])

    def on_application_create(self, application: Application):
        application._client_factory = self._create_api_client

    def create(self):
        self.mesh = ServiceMesh(openshift=self.mesh_oc, identifier=self.identifier,
                                portal_endpoint=self.portal_endpoint)
        credential_name = self.mesh.generate_credentials()
        self.httpbin = Httpbin(openshift=self.httpbin_oc, identifier=self.identifier, credentials=credential_name)

        # pylint: disable=protected-access
        self.env_vars = {name: value.get() for name, value in self.mesh.environ._envs.items()}

    def destroy(self):
        if self.httpbin:
            self.httpbin.destroy()
        if self.mesh:
            self.mesh.environ.set_many(self.env_vars)
            self.mesh.destroy()

    def create_policy(self, name: str, info):
        """Creates new Policy, used for OIDC authorization, for specific realm setup"""
        self.httpbin.create_policy(name, info)

    def remove_policy(self, name: str):
        """Removes existing policy"""
        self.httpbin.remove_policy(name)

    @property
    def environ(self):
        """Returns environ for Service Mesh Gateway"""
        return self.mesh.environ

    # pylint: disable=unused-argument, too-many-arguments
    def _create_api_client(self, application, endpoint, verify, cert=None, disable_retry_status_list=None):
        return ServiceMeshHttpClient(app=application,
                                     cert=cert,
                                     disable_retry_status_list=disable_retry_status_list,
                                     verify=verify,
                                     openshift=self.mesh.openshift,
                                     root_path=self.httpbin.name,
                                     root_url=self.mesh.ingress_url)
