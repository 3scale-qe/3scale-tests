"""Apicast with TLS certificates configured"""
import logging
from abc import ABC, abstractmethod
from typing import Dict
from urllib.parse import urlparse

from threescale_api.resources import Application

from testsuite.openshift.objects import Routes
from .template import TemplateApicastRequirements, TemplateApicast
from ...certificates import Certificate
from ...requirements import CertificateManagerRequirement

LOGGER = logging.getLogger(__name__)


# I am 100% positive that that class is abstract and because of that it doesnt have to implement all the methods..
# pylint: disable=abstract-method, too-many-ancestors
class TLSApicastRequirements(CertificateManagerRequirement, TemplateApicastRequirements, ABC):
    """Requirements for running TLS Apicast"""

    @property
    @abstractmethod
    def server_authority(self) -> Certificate:
        """Returns certificate authority the gateway should use"""


class TLSApicast(TemplateApicast):
    """Gateway deployed with TLS certificates."""

    def __init__(self, requirements: TLSApicastRequirements) -> None:
        super().__init__(requirements)
        self.requirements: TLSApicastRequirements = requirements

        self.service_name = self.deployment
        self.secret_name = f"{self.deployment}-secret"
        self.volume_name = f"{self.deployment}-volume"
        self.mount_path = "/var/apicast/secrets"
        self.https_port = 8443
        self.route_type = Routes.Types.PASSTHROUGH

    @property
    def _hostname(self):
        fragments = urlparse(self.endpoint % "*")
        return fragments.netloc

    @property
    def server_authority(self) -> Certificate:
        """Returns server certificate currently in-use"""
        return self.requirements.server_authority

    @property
    def server_certificate(self) -> Certificate:
        """Returns server certificate currently in-use"""
        return self.requirements.manager.get_or_create("server",
                                                       self._hostname,
                                                       hosts=[self._hostname],
                                                       certificate_authority=self.server_authority)

    def on_application_create(self, application: Application):
        application.api_client_verify = self.server_authority.files["certificate"]

    def get_patch_data(self) -> Dict:
        """Returns patch data for enabling https port on service."""
        return {
            "spec": {
                "ports": [
                    {
                        "name": "https",
                        "port": self.https_port,
                        "protocol": "TCP"
                    }
                ],
            }
        }

    def _add_envs(self):
        LOGGER.debug('Adding envs to deployment "%s"...', self.deployment)

        envs = {
            "APICAST_HTTPS_PORT": self.https_port,
            "APICAST_HTTPS_CERTIFICATE": f"{self.mount_path}/tls.crt",
            "APICAST_HTTPS_CERTIFICATE_KEY": f"{self.mount_path}/tls.key",
        }
        LOGGER.debug(envs)
        self.openshift.environ(self.deployment).set_many(envs)

    def _create_secret(self):
        LOGGER.debug('Creating tls secret "%s"...', self.secret_name)

        cert = self.server_certificate

        self.openshift.secrets.create(
            name=self.secret_name,
            string_data={
                "tls.crt": cert.certificate,
                "tls.key": cert.key
            },
        )

    def create(self):
        """Deploy TLS Apicast."""

        super().create()

        self._create_secret()

        LOGGER.debug('Adding volume "%s" bound to secret "%s" to deployment "%s"...',
                     self.volume_name, self.secret_name, self.deployment)
        self.openshift.add_volume(self.deployment, self.volume_name,
                                  self.mount_path, self.secret_name)

        self._add_envs()

        LOGGER.debug('Patching service "%s". Payload "%s"...', self.service_name, self.get_patch_data())
        self.openshift.patch("service", self.service_name, self.get_patch_data())

        LOGGER.debug('TLS apicast "%s" has been deployed!', self.deployment)

    def destroy(self):
        """Destroy TLS Apicast."""

        super().destroy()

        LOGGER.debug('Deleting secret "%s"', self.secret_name)
        self.openshift.delete("secret", self.secret_name)

        LOGGER.debug('TLS apicast "%s" has been destroyed!', self.deployment)

        self.server_authority.delete_files()
        self.server_certificate.delete_files()
