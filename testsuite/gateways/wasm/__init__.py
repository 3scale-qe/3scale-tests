"""Module containing WASMGateway and its dependencies"""
from typing import Dict
from urllib.parse import urlparse

import importlib_resources as resources
from threescale_api.resources import Service, Application

from testsuite.capabilities import Capability
from testsuite.gateways import AbstractGateway
from testsuite.gateways.service_mesh import ServiceMeshHttpClient
from testsuite.gateways.wasm.extension import WASMExtension
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.env import Properties
from testsuite.utils import generate_tail


# pylint: disable=too-many-instance-attributes
class WASMGateway(AbstractGateway):
    """Gateway for Service mesh 2.1+ configured with 3scale through 3scale-WASM extension"""

    CAPABILITIES = {Capability.SERVICE_MESH, Capability.SERVICE_MESH_WASM}

    # pylint: disable=too-many-arguments
    def __init__(self, httpbin: OpenShiftClient, mesh: OpenShiftClient, portal_endpoint, backend_host, image):
        self.label = generate_tail()
        self.httpbin = httpbin
        self.image = image
        self.mesh = mesh

        res = urlparse(portal_endpoint).netloc.split("@")
        self.portal_host = res[1]
        self.portal_token = res[0]
        self.backend_host = backend_host
        self.base_path = resources.files('testsuite.resources.service_mesh')

        self.extensions: Dict[Service, WASMExtension] = {}

    def before_service(self, service_params: dict) -> dict:
        service_params['deployment_option'] = "service_mesh_istio"
        return service_params

    def on_service_create(self, service: Service):
        self.extensions[service["id"]] = WASMExtension(self.httpbin, self.mesh, self.portal_host, self.portal_token,
                                                       self.backend_host, self.image, self.label, service)

    def on_service_delete(self, service: Service):
        self.extensions[service["id"]].delete()
        del self.extensions[service["id"]]

    def on_application_create(self, application: Application):
        """Override HttpClient"""
        # pylint: disable=protected-access
        application._client_factory = self._create_api_client

    def create(self):
        self.mesh.new_app(self.base_path.joinpath('service_entry.yaml'), {
            "NAME": f"system-entry-{self.label}",
            "LABEL": self.label,
            "HOST": self.portal_host
        })
        self.mesh.new_app(self.base_path.joinpath('service_entry.yaml'), {
            "NAME": f"backend-entry-{self.label}",
            "LABEL": self.label,
            "HOST": self.backend_host
        })

    def destroy(self):
        self.mesh.delete_app(self.label, resources="serviceentry,destinationrule")

    def add_mapping_rules(self, service, rules):
        """Adds mapping rules into the extension, as they do have to be configured separately"""
        ext = self.extensions[service["id"]]
        ext.add_mapping_rules(rules)

    # pylint: disable=unused-argument, too-many-arguments
    def _create_api_client(self, application, endpoint, verify, cert=None, disable_retry_status_list=None):
        ext = self.extensions[application.service["id"]]
        ext.synchronise_mapping_rules()
        ext.synchronise_credentials()

        # wait needed for WASM to load new configuration, fixme: should be replaced with wait for wasm sync
        ext.httpbin.deployment(f"dc/{ext.httpbin_name}").rollout()
        return ServiceMeshHttpClient(app=application,
                                     cert=cert,
                                     disable_retry_status_list=disable_retry_status_list,
                                     verify=verify,
                                     openshift=self.mesh,
                                     root_path=ext.httpbin_name,
                                     root_url=ext.ingress_url)

    @property
    def environ(self) -> Properties:
        """Environ is not yet supported"""
        raise NotImplementedError("Environ is not supported on ServiceMesh")
