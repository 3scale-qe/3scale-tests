"""Self managed apicast deployed from apicast template"""
import logging
import os

import importlib_resources as resources

from testsuite.openshift.objects import SecretTypes
from testsuite.openshift.client import OpenShiftClient
from .selfmanaged import SelfManagedApicast
from ...capabilities import CapabilityRegistry, Capability

LOGGER = logging.getLogger(__name__)


class TemplateApicast(SelfManagedApicast):
    """Template-based APIcast Gateway."""

    # pylint: disable=too-many-arguments
    def __init__(self, staging: bool, openshift: OpenShiftClient, template, name, image,
                 portal_endpoint, generate_name=False, path_routing=False):
        super().__init__(staging, openshift, name, generate_name, path_routing)
        self._image = image
        self._portal_endpoint = portal_endpoint

        if template.endswith(".yml") and template == os.path.basename(template):
            template = resources.files("testsuite.resources").joinpath(template)

        self._template = template
        self.template_parameters = {
            "APICAST_NAME": self.deployment,
            "AMP_APICAST_IMAGE": self._image,
            "CONFIGURATION_URL_SECRET": f"{self.deployment}-secret"}
        if self.staging:
            self.template_parameters.update({
                "CONFIGURATION_LOADER": "lazy",
                "DEPLOYMENT_ENVIRONMENT": "staging",
                "CONFIGURATION_CACHE": 0})

    @staticmethod
    def fits():
        return Capability.OCP3 in CapabilityRegistry()

    def _create_configuration_url_secret(self):
        self.openshift.secrets.create(
            name=self.template_parameters["CONFIGURATION_URL_SECRET"],
            string_data={
                "password": self._portal_endpoint
            },
            secret_type=SecretTypes.BASIC_AUTH
        )

    def create(self):
        LOGGER.debug('Deploying new template-based apicast "%s". Template params: "%s"',
                     self.deployment, self.template_parameters)

        self._create_configuration_url_secret()

        self.openshift.new_app(self._template, self.template_parameters)

        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.deployment)
        super().create()

    def destroy(self):
        super().destroy()
        LOGGER.debug('Destroying template-based apicast "%s"...', self.deployment)

        LOGGER.debug('Deleting service "%s"', self.deployment)
        self.openshift.delete("service", self.deployment)

        LOGGER.debug('Deleting deploymentconfig "%s"', self.deployment)
        self.openshift.delete("deploymentconfig", self.deployment)

        LOGGER.debug('Deleting secret "%s"', self.template_parameters["CONFIGURATION_URL_SECRET"])
        self.openshift.delete("secret", self.template_parameters["CONFIGURATION_URL_SECRET"])

    def connect_jaeger(self, jaeger, jaeger_randomized_name):
        """
        Modifies the APIcast to send information to jaeger.
        Creates configmap and a volume, mounts the configmap into the volume
        Updates the required env vars
        :param jaeger instance of the Jaeger class carrying the information about the apicast_configuration
        :param jaeger_randomized_name: randomized name used for the name of the configmap and for
               the identifying name of the service in jaeger
        """
        service_name = jaeger_randomized_name
        config_map_name = f"{jaeger_randomized_name}.json"
        self.openshift.config_maps.add(config_map_name, jaeger.apicast_config(config_map_name, service_name))
        self.openshift.add_volume(self.deployment, "jaeger-config-vol", "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTRACING_TRACER": "jaeger",
                               "OPENTRACING_CONFIG": f"/tmp/jaeger/{config_map_name}"})
