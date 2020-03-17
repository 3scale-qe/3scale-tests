"""Module containing all baasic gateways"""
import enum
from abc import ABC, abstractmethod
from typing import Dict, List

from threescale_api.resources import Service


class Capability(enum.Enum):
    """Enum containing all known gateway capabilities"""
    PRODUCTION_GATEWAY = "production"
    APICAST = "apicast"
    CUSTOM_ENVIRONMENT = "env"
    SAME_CLUSTER = "internal-cluster"


class AbstractGateway(ABC):
    """Basic gateway for use with Apicast"""

    CAPABILITIES: List[Capability] = []

    def __init__(self, staging: bool, configuration, openshift):
        self.is_staging = staging
        self.configuration = configuration
        self.openshift = openshift

    @abstractmethod
    def get_service_settings(self, service_settings: Dict) -> Dict:
        """Returns finalized settings for service"""

    @abstractmethod
    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        """Returns parameters for proxy"""

    @abstractmethod
    def register_service(self, service: Service):
        """Signals gateway that a new service was created"""

    @abstractmethod
    def unregister_service(self, service: Service):
        """Signals gateway that the service was deleted"""

    @abstractmethod
    def create(self):
        """Starts this gateway"""

    @abstractmethod
    def destroy(self):
        """Destroys gateway"""


class AbstractApicastGateway(AbstractGateway):
    """Interface defining basic functionality of an Apicast gateway"""

    CAPABILITIES = [Capability.APICAST]

    @abstractmethod
    def set_env(self, name: str, value):
        """Sets the value of environmental variable"""

    @abstractmethod
    def get_env(self, name: str):
        """Gets the value of environmental variable"""

    @abstractmethod
    def reload(self):
        """Reloads gateway"""

    def register_service(self, service: Service):
        pass

    def unregister_service(self, service: Service):
        pass

    def create(self):
        pass

    def destroy(self):
        pass
