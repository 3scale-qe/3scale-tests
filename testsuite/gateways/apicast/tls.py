"""Apicast with TLS certificates configured"""
import base64
import logging
from abc import ABC
from typing import Dict
from urllib.parse import urlparse

from threescale_api.resources import Service

from testsuite.certificates import GetCertificateResponse, CreateCertificateResponse
from testsuite.openshift.objects import Routes
from testsuite.requirements import CFSSLRequirement

from .template import TemplateApicastRequirements, TemplateApicast

LOGGER = logging.getLogger(__name__)


# I am 100% positive that that class is abstract and because of that it doesnt have to implement all the methods..
# pylint: disable=abstract-method, too-many-ancestors
class TLSApicastRequirements(CFSSLRequirement, TemplateApicastRequirements, ABC):
    """Requirements for running TLS Apicast"""


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

    @property
    def endpoint(self):
        """Returns gateway endpoint."""
        return self.staging_endpoint if self.staging else self.production_endpoint

    @property
    def hostname(self):
        """Returns wildcard endpoint."""
        return urlparse(self.endpoint % "*").hostname

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        entity_id = service.entity_id
        proxy_settings.update({
            "sandbox_endpoint": self.staging_endpoint % f"{entity_id}-staging",
            "endpoint": self.production_endpoint % f"{entity_id}-production",
        })
        return proxy_settings

    def register_service(self, service: Service):
        service_id = service.entity_id

        staging_name = f"{service_id}-staging"
        prod_name = f"{service_id}-production"

        staging_endpoint = urlparse(self.staging_endpoint % staging_name).hostname
        production_endpoint = urlparse(self.production_endpoint % prod_name).hostname

        LOGGER.debug('Creating routes for service "%s"', self.service_name)

        self.openshift.routes.create(staging_name, Routes.Types.PASSTHROUGH,
                                     service=self.service_name, hostname=staging_endpoint)
        self.openshift.routes.create(prod_name, Routes.Types.PASSTHROUGH,
                                     service=self.service_name, hostname=production_endpoint)

    def unregister_service(self, service: Service):
        service_id = service.entity_id

        LOGGER.debug('Deleting routes for service "%s"', self.service_name)

        del self.openshift.routes[f"{service_id}-staging"]
        del self.openshift.routes[f"{service_id}-production"]

    @property
    def _csr_names(self):
        """Returns data for Certificate Signing Request."""
        return {
            "O": self.hostname,
            "OU": "IT",
            "L": "San Francisco",
            "ST": "California",
            "C": "US",
        }

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

        cert = self.new_cert("server")

        pem = cert.certificate.encode("ascii")
        key = cert.key.encode("ascii")

        resource = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": self.secret_name,
            },
            "data": {
                "tls.crt": base64.b64encode(pem).decode("ascii"),
                "tls.key": base64.b64encode(key).decode("ascii"),
            }
        }

        self.openshift.apply(resource)

    def new_cert(self, label: str) -> CreateCertificateResponse:
        """Create a new ssl certificate.
        Args:
            :param label: A identifier forthe certificate.
        Returns:
            certificate: Certificate PEM-like.
            private_key: Key PEM-like.
        """
        return self.requirements.manager.create(label, self.hostname, hosts=[self.hostname],
                                                names=[self._csr_names])

    def get_cert(self, label: str) -> GetCertificateResponse:
        """Get existent certificate.
        Args:
            :param label: A identifier for the certificate.
        Returns:
            certificate: Certificate PEM-like.
            private_key: Key PEM-like.
        """
        return self.requirements.certificate_store.get(label)

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
