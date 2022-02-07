"""Apicast with TLS certificates configured"""
import logging
from typing import Dict

from threescale_api.resources import Application

from testsuite.openshift.objects import Routes, SecretKinds
from .template import TemplateApicast
from ...certificates import Certificate
from ...openshift.client import OpenShiftClient

LOGGER = logging.getLogger(__name__)


class TLSApicast(TemplateApicast):
    """APIcast deployed with TLS certificates."""

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(self, staging: bool, openshift: OpenShiftClient, template, name, image, portal_endpoint, superdomain,
                 server_authority, manager, generate_name=False, path_routing=False) -> None:
        super().__init__(staging, openshift, template, name, image, portal_endpoint, generate_name, path_routing)
        self.service_name = self.deployment.name
        self.superdomain = superdomain
        self.server_authority = server_authority
        self.manager = manager
        self.secret_name = f"{self.deployment.name}-server-authority"
        self.volume_name = f"{self.deployment.name}-volume"
        self.mount_path = "/var/apicast/secrets"
        self.https_port = 8443

    @property
    def _hostname(self):
        return f"*.{self.superdomain}"

    @property
    def server_certificate(self) -> Certificate:
        """Returns server certificate currently in-use"""
        return self.manager.get_or_create("server",
                                          self._hostname,
                                          hosts=[self._hostname],
                                          certificate_authority=self.server_authority)

    def add_route(self, name, kind=Routes.Types.PASSTHROUGH):
        """Adds new route for this APIcast"""
        hostname = f"{name}.{self.superdomain}"
        result = self.openshift.routes.create(name, kind, hostname=hostname,
                                              service=self.deployment.name, port="https")
        self._routes.append(name)
        return result

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
        self.environ.set_many(envs)

    def _create_secret(self):
        LOGGER.debug('Creating tls secret "%s"...', self.secret_name)

        self.openshift.secrets.create(name=self.secret_name, kind=SecretKinds.TLS, certificate=self.server_certificate)

    def create(self):
        """Deploy TLS Apicast."""

        super().create()

        self._create_secret()

        LOGGER.debug('Adding volume "%s" bound to secret "%s" to deployment "%s"...',
                     self.volume_name, self.secret_name, self.deployment)
        self.deployment.add_volume(self.volume_name, self.mount_path, self.secret_name)

        self._add_envs()

        LOGGER.debug('Patching service "%s". Payload "%s"...', self.service_name, self.get_patch_data())
        self.openshift.patch("service", self.service_name, self.get_patch_data())

        LOGGER.debug('TLS apicast "%s" has been deployed!', self.deployment)

    def destroy(self):
        """Destroy TLS Apicast."""

        super().destroy()

        LOGGER.debug('Deleting secret "%s"', self.secret_name)
        self.openshift.delete("secret", self.secret_name)

        LOGGER.debug('TLS apicast "%s" has been destroyed!', self.deployment.name)

        self.server_certificate.delete_files()
