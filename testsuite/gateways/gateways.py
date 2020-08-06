"""Module containing all basic gateways"""
import enum
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

from testsuite.openshift.env import Environ
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
    PRODUCTION_GATEWAY = "production"           # Allows production gateway with reload() capability
    APICAST = "apicast"                         # Is Apicast, this is mutually exclusive with Service Mesh
    CUSTOM_ENVIRONMENT = "env"                  # Allows environment manipulation through environ() method
    SAME_CLUSTER = "internal-cluster"           # Is always located on the same cluster as 3scale
    SERVICE_MESH = "service-mesh"               # Is Service Mesh, this is mutually exclusive with Apicast
    STANDARD_GATEWAY = "standard"               # Tests which deploy their own gateway will run


class AbstractGateway(LifecycleHook, ABC):
    """Basic gateway for use with Apicast"""

    CAPABILITIES: List[Capability] = []

    @property
    def environ(self) -> Environ:
        """Returns environ object for given gateway"""
        raise NotImplementedError()

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
    def reload(self):
        """Reloads gateway"""

    @abstractmethod
    def get_logs(self):
        """Gets the pod logs for the newest deployment"""

    def create(self):
        pass

    def destroy(self):
        pass
