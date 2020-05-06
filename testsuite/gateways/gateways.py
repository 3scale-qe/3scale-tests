"""Module containing all basic gateways"""
import enum
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

from testsuite.requirements import OpenshiftRequirement
from testsuite.lifecycle_hook import LifecycleHook

if TYPE_CHECKING:
    from testsuite.openshift.client import OpenShiftClient


class GatewayRequirements(OpenshiftRequirement, ABC):
    """Requirements for running gateways"""

    @property
    @abstractmethod
    def staging(self) -> bool:
        """Returns if the current gateway is staging or production"""

    @property
    @abstractmethod
    def current_openshift(self) -> "OpenShiftClient":
        """Returns currently configured openshift"""


class Capability(enum.Enum):
    """Enum containing all known gateway capabilities"""
    PRODUCTION_GATEWAY = "production"
    APICAST = "apicast"
    CUSTOM_ENVIRONMENT = "env"
    SAME_CLUSTER = "internal-cluster"
    SERVICE_MESH = "service-mesh"


class AbstractGateway(LifecycleHook, ABC):
    """Basic gateway for use with Apicast"""

    CAPABILITIES: List[Capability] = []

    @abstractmethod
    def create(self):
        """Starts this gateway"""

    @abstractmethod
    def destroy(self):
        """Destroys gateway"""


class AbstractApicast(AbstractGateway, ABC):
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

    def create(self):
        pass

    def destroy(self):
        pass
