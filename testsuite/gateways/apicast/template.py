"""Self managed apicast deployed from apicast template"""

import logging
import os

import importlib_resources as resources

from testsuite.openshift.objects import SecretTypes
from testsuite.openshift.client import OpenShiftClient
from . import OpenshiftApicast

LOGGER = logging.getLogger(__name__)


class TemplateApicast(OpenshiftApicast):
    """Template-based APIcast Gateway."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        staging: bool,
        openshift: OpenShiftClient,
        template,
        name,
        image,
        portal_endpoint,
        generate_name=False,
        path_routing=False,
    ):
        super().__init__(staging, openshift, name, generate_name, path_routing)
        self._image = image
        self._portal_endpoint = portal_endpoint

        if template.endswith(".yml") and template == os.path.basename(template):
            template = resources.files("testsuite.resources").joinpath(template)

        self._template = template
        self.template_parameters = {
            "APICAST_NAME": self.deployment.name,
            "AMP_APICAST_IMAGE": self._image,
            "CONFIGURATION_URL_SECRET": f"{self.deployment.name}-secret",
        }
        if self.staging:
            self.template_parameters.update(
                {"CONFIGURATION_LOADER": "lazy", "DEPLOYMENT_ENVIRONMENT": "staging", "CONFIGURATION_CACHE": 0}
            )

    @staticmethod
    def fits(openshift: OpenShiftClient):  # pylint: disable=unused-argument
        return True

    def _create_configuration_url_secret(self):
        self.openshift.secrets.create(
            name=self.template_parameters["CONFIGURATION_URL_SECRET"],
            string_data={"password": self._portal_endpoint},
            secret_type=SecretTypes.BASIC_AUTH,
        )

    def create(self):
        LOGGER.debug(
            'Deploying new template-based apicast "%s". Template params: "%s"',
            self.deployment,
            self.template_parameters,
        )

        self._create_configuration_url_secret()

        self.openshift.new_app(self._template, self.template_parameters)

        # pylint: disable=protected-access
        self.deployment.wait_for()
        super().create()

    def destroy(self):
        super().destroy()
        LOGGER.debug('Destroying template-based apicast "%s"...', self.deployment)

        LOGGER.debug('Deleting service "%s"', self.deployment)
        self.openshift.delete("service", self.deployment.name)

        LOGGER.debug('Deleting deploymentconfig "%s"', self.deployment)
        self.deployment.delete()

        LOGGER.debug('Deleting secret "%s"', self.template_parameters["CONFIGURATION_URL_SECRET"])
        self.openshift.delete("secret", self.template_parameters["CONFIGURATION_URL_SECRET"])

    def setup_tls(self, secret_name, https_port):
        mount_path = "/var/apicast/secrets"
        LOGGER.debug('Adding tls volume bound to secret "%s" to deployment "%s"...', secret_name, self.deployment)
        self.deployment.add_volume("tls-secret", mount_path, secret_name)

        LOGGER.debug('Patching https port into service "%s"...', self.deployment)
        self.openshift.patch(
            "service",
            self.deployment.name,
            [
                {
                    "op": "add",
                    "path": "/spec/ports/-",
                    "value": {"name": "httpsproxy", "port": https_port, "protocol": "TCP"},
                }
            ],
            patch_type="json",
        )

        LOGGER.debug('Adding envs to deployment "%s"...', self.deployment)
        self.environ.set_many(
            {
                "APICAST_HTTPS_PORT": https_port,
                "APICAST_HTTPS_CERTIFICATE": f"{mount_path}/tls.crt",
                "APICAST_HTTPS_CERTIFICATE_KEY": f"{mount_path}/tls.key",
            }
        )
