"""Module managing testsuite capabilities

Capability is set of (usually) strings which tell us which features are available on this test environment.
In tests you can use it with pytest.mark.require_capabilities(capability1, capability2, ...)

Capabilities are provider by a functions annotated with @capability_provider and should return Set of capabilities
"""
import enum
from functools import reduce
from typing import Set, Callable, Any, Optional

# Users should have access only to these public methods/decorators
__all__ = ["CapabilityRegistry", "Capability"]


class Capability(enum.Enum):
    """Enum containing all known environment capabilities"""
    PRODUCTION_GATEWAY = "production"           # Allows production gateway with reload() capability
    APICAST = "apicast"                         # Is Apicast, this is mutually exclusive with Service Mesh
    CUSTOM_ENVIRONMENT = "env"                  # Allows environment manipulation through environ() method
    SAME_CLUSTER = "internal-cluster"           # Is always located on the same cluster as 3scale
    SERVICE_MESH = "service-mesh"               # Is Service Mesh, this is mutually exclusive with Apicast
    STANDARD_GATEWAY = "standard"               # Tests which deploy their own gateway will run
    LOGS = "logs"                               # Allows getting apicast logs through get_logs() method
    JAEGER = "jaeger"                           # Allows configuring the Apicast to send data to Jaeger


class _CapabilityRegistry:
    instance: 'Optional[_CapabilityRegistry]' = None

    def __init__(self) -> None:
        super().__init__()
        self.providers: Set[Callable[[], Set[Any]]] = set()
        self._capabilities = None

    @property
    def capabilities(self):
        """Returns all capabilites"""
        if self._capabilities is None:
            self._capabilities = set()
            reduce(lambda result, provider: result.update(provider()), self.providers, self._capabilities)
        return self._capabilities

    def register_provider(self, provider: Callable[[], Set[Any]]):
        """Register new capability provider"""
        self.providers.add(provider)

    def __contains__(self, item):
        return item in self.capabilities


# pylint: disable=invalid-name
def CapabilityRegistry() -> _CapabilityRegistry:
    """Returns singleton instance of CapabilityRegistry"""
    if _CapabilityRegistry.instance is None:
        _CapabilityRegistry.instance = _CapabilityRegistry()
    return _CapabilityRegistry.instance
