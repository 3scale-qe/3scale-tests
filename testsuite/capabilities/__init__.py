"""Module managing testsuite capabilities

Capability is set of (usually) strings which tell us which features are available on this test environment.
In tests you can use it with pytest.mark.required_capabilities(capability1, capability2, ...)

Capabilities are provider by a functions annotated with @capability_provider and should return Set of capabilities
"""

import enum
from typing import Any, Callable, List, Set, Tuple

# Users should have access only to these public methods/decorators
__all__ = ["CapabilityRegistry", "Capability"]


class Capability(enum.Enum):
    """Enum containing all known environment capabilities"""

    # fmt: off
    PRODUCTION_GATEWAY = "production"           # Allows production gateway with reload() capability
    APICAST = "apicast"                         # Is APIcast, this is mutually exclusive with Service Mesh
    CUSTOM_ENVIRONMENT = "env"                  # Allows environment manipulation through environ() method
    SAME_CLUSTER = "internal-cluster"           # Is always located on the same cluster as 3scale
    SERVICE_MESH = "service-mesh"               # It is running through Service Mesh
    SERVICE_MESH_WASM = "wasm"                  # It is running through WASM extension with ServiceMesh 2.1
    SERVICE_MESH_ADAPTER = "adapter"            # It is running through Istio adapter with Service Mesh 2.0
    STANDARD_GATEWAY = "standard"               # Tests which deploy their own gateway will run
    LOGS = "logs"                               # Allows getting APIcast logs through get_logs() method
    JAEGER = "jaeger"                           # Allows configuring the APIcast to send data to Jaeger
    OCP4 = "ocp4"                               # If the current environment is OpenShift 4
    OCP3 = "ocp3"                               # If the current environment is OpenShift 3
    SCALING = "scaling"                         # If the current environment supports scaling of components
    # fmt: on


class Singleton(type):
    """Metaclass for creating Singletons"""

    def __init__(cls, name, bases, mmbs):
        super().__init__(name, bases, mmbs)
        cls._instance = super().__call__()

    def __call__(cls, *args, **kw):
        return cls._instance


Provider = Callable[[], Set[Any]]


class CapabilityRegistry(metaclass=Singleton):
    """Registry for all the capabilities testsuite has"""

    def __init__(self) -> None:
        super().__init__()
        self.providers: List[Tuple[Set[Any], Provider]] = []
        self.discovered: Set[Any] = set()
        self.capabilities: Set[Any] = set()

    def register_provider(self, provider: Provider, provides: Set[Any]):
        """Register new capability provider"""
        self.providers.append((provides, provider))

    def _find_provider(self, capability):
        """
        Returns provider and all capabilities it can provide based on the capability requested
        Runs in O(n) due to discrepancy between discovered capabilities (=those whose providers have been run)
        and actual capabilities (=those that are present). Still faster than if all providers were run at all times.
        """
        for capabilities, provider in self.providers:
            if capability in capabilities:
                return capabilities, provider
        return None

    def __contains__(self, item):
        if item not in self.discovered:
            capabilities, provider = self._find_provider(item)
            if provider is None:
                # Capability is unknown and not provided by anyone
                return False
            new_capabilities = provider()
            self.discovered.update(capabilities)
            self.capabilities.update(new_capabilities)
        return item in self.capabilities
