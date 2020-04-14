"""Contains implementations for all Gateway Requirements for current testsuite"""
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from testsuite import CommonConfiguration
from testsuite.certificates import CertificateManager, CertificateStore, Certificate
from testsuite.gateways.apicast import SystemApicastRequirements, OperatorApicastRequirements, \
    TemplateApicastRequirements, TLSApicastRequirements
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicastRequirements
from testsuite.gateways.gateways import GatewayRequirements

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
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
    def staging_endpoint(self) -> str:
        return self.setting_block["staging_endpoint"]

    @property
    def production_endpoint(self) -> str:
        return self.setting_block["production_endpoint"]

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
    def _services(self):
        return self.setting_block.get("services", {})

    @property
    def staging_service(self):
        return self._services.get("staging", "apicast-staging")

    @property
    def production_service(self):
        return self._services.get("production", "apicast-production")


class TemplateApicastOptions(SelfManagedApicastOptions, TemplateApicastRequirements):
    """Implementation of TemplateApicastRequirements"""
    @property
    def staging_endpoint(self) -> str:
        try:
            return super().staging_endpoint
        except KeyError:
            wildcard_domain = self.current_openshift.config_maps["system-environment"]["THREESCALE_SUPERDOMAIN"]
            return f"http://%s-staging.{wildcard_domain}"

    @property
    def production_endpoint(self) -> str:
        try:
            return super().production_endpoint
        except KeyError:
            wildcard_domain = self.current_openshift.config_maps["system-environment"]["THREESCALE_SUPERDOMAIN"]
            return f"http://%s-production.{wildcard_domain}"

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
    def certificate(self) -> Certificate:
        return self.configuration.certificate

    @property
    def certificate_store(self) -> CertificateStore:
        return self.configuration.certificate_store

    @property
    def manager(self) -> CertificateManager:
        return self.configuration.manager
