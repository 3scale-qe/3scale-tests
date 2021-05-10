"""Self managed apicast deployed from apicast template"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, List
from urllib.parse import urlparse

from threescale_api.resources import Service
import importlib_resources as resources

from testsuite.openshift.objects import Routes, SecretTypes
from testsuite.requirements import ThreeScaleAuthDetails
from .selfmanaged import SelfManagedApicast, SelfManagedApicastRequirements, SelfManagedApicast2
from ...openshift.env import Environ

LOGGER = logging.getLogger(__name__)


class TemplateApicastRequirements(SelfManagedApicastRequirements,
                                  ThreeScaleAuthDetails,
                                  ABC):
    """Requirements for TemplateApicast"""
    @property
    @abstractmethod
    def template(self):
        """Returns template file"""

    @property
    @abstractmethod
    def image(self):
        """Return image to use with in the template"""

    @property
    @abstractmethod
    def configuration_url(self):
        """Returns URL for configuring apicast"""

    @property
    @abstractmethod
    def service_routes(self) -> bool:
        """True, if apicast should creates route for every service"""


class TemplateApicast2(SelfManagedApicast2):
    """Template-based Apicast Gateway."""
    # pylint: disable=too-many-arguments
    def __init__(self, openshift, template, name, image, portal_endpoint):
        super().__init__(openshift, name)
        self._image = image
        self._portal_endpoint = portal_endpoint

        if template.endswith(".yml") and template == os.path.basename(template):
            template = resources.files("testsuite.resources").joinpath(template)

        self._template = template

    @property
    def _params(self):
        params = {
            "APICAST_NAME": self.name,
            "AMP_APICAST_IMAGE": self._image,
            "CONFIGURATION_URL_SECRET": f"{self.name}-secret"}
        if self.staging:
            params.update({
                "CONFIGURATION_LOADER": "lazy",
                "DEPLOYMENT_ENVIRONMENT": "staging",
                "CONFIGURATION_CACHE": 0})
        return params

    def _create_connection_secret(self):
        self._oc.secrets.create(
            name=self._params["CONFIGURATION_URL_SECRET"],
            string_data={
                "password": self._portal_endpoint
            },
            secret_type=SecretTypes.BASIC_AUTH
        )

    def create(self):
        LOGGER.debug('Deploying new template-based apicast "%s". Template params: "%s"',
                     self.name, self._params)

        self._create_connection_secret()

        self._oc.new_app(self._template, self._params)

        # pylint: disable=protected-access
        self._oc._wait_for_deployment(self.name)

    def destroy(self):
        LOGGER.debug('Destroying template-based apicast "%s"...', self.name)

        for route in self._routes:
            if route in self._oc.routes:
                LOGGER.debug('Removing route "%s"...', route)
                del self._oc.routes[route]

        LOGGER.debug('Deleting service "%s"', self.name)
        self._oc.delete("service", self.name)

        LOGGER.debug('Deleting deploymentconfig "%s"', self.name)
        self._oc.delete("deploymentconfig", self.name)

        LOGGER.debug('Deleting secret "%s"', self._params["CONFIGURATION_URL_SECRET"])
        self._oc.delete("secret", self._params["CONFIGURATION_URL_SECRET"])


# pylint: disable=too-many-instance-attributes
class TemplateApicast(SelfManagedApicast):
    """Template-based Apicast Gateway."""

    def __init__(self, requirements: TemplateApicastRequirements) -> None:
        super().__init__(requirements)
        self.requirements = requirements
        self.template = requirements.template
        self.image = requirements.image
        self.service_routes = requirements.service_routes
        self.service_name = self.deployment
        self.name = self.deployment
        self.configuration_url_secret_name = f'{self.deployment}-config-url'
        self.routes: List[str] = []
        self.route_type = Routes.Types.EDGE

    def get_app_params(self, **kwargs):
        """Template envs for oc new-app."""
        params = {
            "APICAST_NAME": self.deployment,
            "AMP_APICAST_IMAGE": self.image,
            "DEPLOYMENT_ENVIRONMENT": "production",
            "CONFIGURATION_LOADER": "boot",
            "CONFIGURATION_CACHE": 300,
            "LOG_LEVEL": "info",
            "CONFIGURATION_URL_SECRET": self.configuration_url_secret_name,
        }

        if self.staging:
            params.update({
                "CONFIGURATION_LOADER": "lazy",
                "DEPLOYMENT_ENVIRONMENT": "staging",
                "CONFIGURATION_CACHE": 0,
            })

        params.update(**kwargs)

        return params

    def _create_configuration_url_secret(self):
        self.openshift.secrets.create(
            name=self.configuration_url_secret_name,
            string_data={
                "password": self.requirements.configuration_url
            },
            secret_type=SecretTypes.BASIC_AUTH
        )

    def _route_name(self, entity_id):
        if self.staging:
            return f"{entity_id}-staging"
        return f"{entity_id}-production"

    def on_service_create(self, service: Service):
        super().on_service_create(service)
        if self.service_routes:
            entity_id = service.entity_id
            self.add_route(entity_id, self._route_name(entity_id))

    def on_service_delete(self, service: Service):
        super().on_service_delete(service)
        if self.service_routes:
            self.delete_route(self._route_name(service.entity_id))

    @property
    def environ(self) -> Environ:
        return self.openshift.environ(self.deployment)

    def add_route(self, url_fragment, name: Optional[str] = None):
        """Adds new route for this apicast"""
        identifier = name or url_fragment
        url = urlparse(self.endpoint % url_fragment)
        if url.scheme == "https":
            self.openshift.routes.create(identifier, self.route_type,
                                         service=self.service_name, hostname=url.hostname)
        elif url.scheme == "http":
            self.openshift.routes.expose(name=identifier,
                                         service=self.service_name, hostname=url.hostname)
        else:
            raise AttributeError(f"Unknown scheme {url.scheme} for apicast route")
        self.routes.append(identifier)

    def delete_route(self, identifier):
        """Delete route"""
        if identifier in self.routes and identifier in self.openshift.routes:
            del self.openshift.routes[identifier]
            self.routes.remove(identifier)

    def create(self):
        LOGGER.debug('Deploying new template-based apicast "%s". Template params: "%s"',
                     self.deployment, self.get_app_params())

        self._create_configuration_url_secret()

        self.openshift.new_app(self.template, self.get_app_params())

        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.deployment)

    def destroy(self):
        LOGGER.debug('Destroying template-based apicast "%s"...', self.deployment)

        for route in self.routes:
            if route in self.openshift.routes:
                LOGGER.debug('Removing route "%s"...', route)
                del self.openshift.routes[route]

        LOGGER.debug('Deleting service "%s"', self.deployment)
        self.openshift.delete("service", self.deployment)

        LOGGER.debug('Deleting deploymentconfig "%s"', self.deployment)
        self.openshift.delete("deploymentconfig", self.deployment)

        LOGGER.debug('Deleting secret "%s"', self.configuration_url_secret_name)
        self.openshift.delete("secret", self.configuration_url_secret_name)
