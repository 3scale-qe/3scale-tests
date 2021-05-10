"""Module managing testsuite capabilities

Capability is set of (usually) strings which tell us which features are available on this test environment.
In tests you can use it with pytest.mark.require_capabilities(capability1, capability2, ...)

Capabilities are provider by a functions annotated with @capability_provider and should return Set of capabilities
"""
import enum
from typing import Set, Callable, Any

# Users should have access only to these public methods/decorators
__all__ = ["CapabilityRegistry", "Capability"]


class Capability(enum.Enum):
    """Enum containing all known environment capabilities"""
    PRODUCTION_GATEWAY = "production"           # Allows production gateway with reload() capability
    APICAST = "apicast"                         # Is APIcast, this is mutually exclusive with Service Mesh
    CUSTOM_ENVIRONMENT = "env"                  # Allows environment manipulation through environ() method
    SAME_CLUSTER = "internal-cluster"           # Is always located on the same cluster as 3scale
    SERVICE_MESH = "service-mesh"               # Is Service Mesh, this is mutually exclusive with Apicast
    STANDARD_GATEWAY = "standard"               # Tests which deploy their own gateway will run
    LOGS = "logs"                               # Allows getting APIcast logs through get_logs() method
    JAEGER = "jaeger"                           # Allows configuring the APIcast to send data to Jaeger
    OCP4 = "ocp4"                               # If the current environment is OpenShift 4
    OCP3 = "ocp3"                               # If the current environment is OpenShift 3
    SCALING = "scaling"                         # If the current environment supports scaling of components


class Singleton(type):
    """Metaclass for creating Singletons"""
    def __init__(cls, name, bases, mmbs):
        super().__init__(name, bases, mmbs)
        cls._instance = super().__call__()

    def __call__(cls, *args, **kw):
        return cls._instance


class CapabilityRegistry(metaclass=Singleton):
    """Registry for all the capabilities testsuite has"""
    def __init__(self) -> None:
        super().__init__()
        self.providers: Set[Callable[[], Set[Any]]] = set()
        self._capabilities = None

    @property
    def capabilities(self):
        """Returns all capabilites"""
        if self._capabilities is None:
            sets = [provider() for provider in self.providers]
            self._capabilities = set().union(*sets)
        return self._capabilities

    def register_provider(self, provider: Callable[[], Set[Any]]):
        """Register new capability provider"""
        self.providers.add(provider)

    def __contains__(self, item):
        return item in self.capabilities
