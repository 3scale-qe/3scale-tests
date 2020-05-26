"""Conftest for Service Mesh RHSSO tests"""
import pytest
from threescale_api.resources import Service

from testsuite.gateways import ServiceMeshGateway
from testsuite.lifecycle_hook import LifecycleHook
from testsuite.rhsso.rhsso import OIDCClientAuthHook, OIDCClientAuth


# pylint: disable=too-few-public-methods
class ServiceMeshOIDCClientAuth(OIDCClientAuth):
    """Authentication class for OIDC based authorization for ServiceMesh"""

    def __call__(self, application):
        super_process = super().__call__(application)

        def _process_request(request):
            app_key = application.keys.list()["keys"][0]["key"]["value"]
            request.prepare_url(request.url, {"app_key": app_key})
            return super_process(request)

        return _process_request


# pylint: disable=too-few-public-methods
class ServiceMeshRHSSOHook(OIDCClientAuthHook, LifecycleHook):
    """RHSSO hook used for Service Mesh"""

    def __init__(self, rhsso_service_info, gateway: ServiceMeshGateway):
        super().__init__(rhsso_service_info, "authorization")
        self.httpbin = gateway.httpbin

    # pylint: disable=no-self-use
    def _create_name(self, entity_id):
        return f"policy-{entity_id}"

    def on_service_create(self, service):
        super().on_service_create(service)
        self.httpbin.create_policy(self._create_name(service.entity_id), self.rhsso_service_info)

    def on_service_delete(self, service: Service):
        self.httpbin.remove_policy(self._create_name(service.entity_id))

    def on_application_create(self, application):
        """Register OIDC auth object for api_client"""

        application.register_auth("oidc",
                                  ServiceMeshOIDCClientAuth(self.rhsso_service_info, self.credentials_location))


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info, staging_gateway):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(ServiceMeshRHSSOHook(rhsso_service_info, staging_gateway))
