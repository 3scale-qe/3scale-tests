"""Contains implementations for all Gateway Requirements for current testsuite"""
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from weakget import weakget

from testsuite.config import settings
from testsuite import CommonConfiguration
from testsuite.certificates import CertificateManager, CertificateStore, Certificate
from testsuite.gateways.apicast import SystemApicastRequirements, OperatorApicastRequirements, \
    TemplateApicastRequirements, TLSApicastRequirements
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicastRequirements
from testsuite.gateways.gateways import GatewayRequirements
from testsuite.gateways.service_mesh import ServiceMeshRequirements, HttpbinFactory, ServiceMeshFactory
from testsuite.requirements import ThreeScaleAuthDetails

if TYPE_CHECKING:
    from testsuite.openshift.client import OpenShiftClient


class GatewayOptions(GatewayRequirements):
    """Implementation of GatewayRequirements in current testsuite"""

    def __init__(self, staging: bool, settings_block, configuration: CommonConfiguration) -> None:
        self.setting_block = settings_block
        self.configuration = configuration
        self.project = self.setting_block.get("project", "threescale")
        self.server = self.setting_block.get("server", "default")
        self._staging = staging

    @property
    def staging(self) -> bool:
        return self._staging

    @property
    def current_openshift(self) -> "OpenShiftClient":
        return self.openshift(self.server, self.project)

    def openshift(self, server="default", project="threescale") -> "OpenShiftClient":
        return self.configuration.openshift(server, project)

    @property
    def print_logs(self) -> bool:
        return weakget(settings)["reporting"]["print_app_logs"] % True


class SystemApicastOptions(GatewayOptions, SystemApicastRequirements):
    """Implementation of SystemApicastRequirements in current testsuite"""

    @property
    def staging_deployment(self) -> str:
        return self.setting_block.get("staging_deployment", "apicast-staging")

    @property
    def production_deployment(self) -> str:
        return self.setting_block.get("production_deployment", "apicast-production")


class SelfManagedApicastOptions(GatewayOptions, SelfManagedApicastRequirements):
    """Implementation of SelfManagedApicastRequirements with current testsuite"""

    @property
    def _deployments(self):
        return self.setting_block["deployments"]

    @property
    def _endpoints(self):
        return self.setting_block["endpoints"]

    @property
    def staging_endpoint(self) -> str:
        return self._endpoints["staging"]

    @property
    def production_endpoint(self) -> str:
        return self._endpoints["production"]

    @property
    def staging_deployment(self) -> str:
        return self._deployments["staging"]

    @property
    def production_deployment(self) -> str:
        return self._deployments["production"]


# pylint: disable=too-many-ancestors
class OperatorApicastOptions(SelfManagedApicastOptions, OperatorApicastRequirements):
    """Implementation of OperatorApicastRequirements with current testsuite"""

    @property
    def auth_details(self) -> ThreeScaleAuthDetails:
        return self.configuration


class TemplateApicastOptions(SelfManagedApicastOptions, TemplateApicastRequirements):
    """Implementation of TemplateApicastRequirements"""

    @property
    def service_routes(self) -> bool:
        return self.setting_block.get("service_routes", True)

    @property
    def staging_endpoint(self) -> str:
        try:
            return super().staging_endpoint
        except KeyError:
            return f"https://%s-staging.{self.configuration.superdomain}"

    @property
    def production_endpoint(self) -> str:
        try:
            return super().production_endpoint
        except KeyError:
            return f"https://%s-production.{self.configuration.superdomain}"

    @property
    def template(self):
        return self.configuration.gateway_template

    @property
    def image(self):
        return self.configuration.gateway_image

    @property
    def configuration_url(self):
        try:
            url = self.setting_block["apicast-configuration-url"]
        except KeyError:
            admin_url = urlparse(self.url)
            url = f"https://{self.token}@{admin_url.hostname}"
        return url.encode("utf-8")

    @property
    def token(self) -> str:
        return self.configuration.token

    @property
    def url(self) -> str:
        return self.configuration.url


class TLSApicastOptions(TemplateApicastOptions, TLSApicastRequirements):
    """Implementation of TLSApicastRequirements"""

    @property
    def _default_endpoint(self):
        return f"https://%s.{self.configuration.superdomain}"

    @property
    def staging_endpoint(self) -> str:
        try:
            return self.setting_block["staging_endpoint"]
        except KeyError:
            return self._default_endpoint

    @property
    def production_endpoint(self) -> str:
        try:
            return self.setting_block["production_endpoint"]
        except KeyError:
            return self._default_endpoint

    @property
    def certificate(self) -> Certificate:
        return self.configuration.certificate

    @property
    def certificate_store(self) -> CertificateStore:
        return self.configuration.certificate_store

    @property
    def manager(self) -> CertificateManager:
        return self.configuration.manager


class ServiceMeshGatewayOptions(GatewayOptions, ServiceMeshRequirements):
    """Options for Service mesh gateway"""

    @property
    def _server(self):
        return self.setting_block.get("server", "default")

    @property
    def httpbin_factory(self) -> HttpbinFactory:
        conf = self.setting_block.get("httpbin", {})
        openshift = self.openshift(server=self._server, project=conf.get("project", "httpbin"))
        return HttpbinFactory(openshift=openshift)

    @property
    def mesh_factory(self) -> ServiceMeshFactory:
        conf = self.setting_block.get("mesh", {})
        openshift = self.openshift(server=self._server, project=conf.get("project", "service-mesh"))
        return ServiceMeshFactory(openshift=openshift,
                                  token=self.configuration.token,
                                  url=self.configuration.url)
