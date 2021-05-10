"""
Sets up gateway defined in testsuite settings
"""
from typing import Tuple, Optional, Dict, Type, NamedTuple
import importlib
import inspect
import pkgutil

from testsuite.config import settings
from testsuite.gateways.apicast import SystemApicast, SelfManagedApicast, OperatorApicast, TemplateApicast, TLSApicast
from testsuite.gateways.apicast.containers import ContainerizedApicast
from testsuite.gateways.gateways import AbstractGateway
from testsuite.gateways.options import GatewayOptions, SystemApicastOptions, SelfManagedApicastOptions, \
    OperatorApicastOptions, TemplateApicastOptions, TLSApicastOptions, ServiceMeshGatewayOptions
from testsuite.gateways.service_mesh import ServiceMeshGateway

# walk through all sub-packages and import all gateway classes
__all__ = ["gateway", "Gateway", "Options", "GATEWAYS", "GatewayConfiguration", "load_gateway", "configuration"]
for _, module, _ in pkgutil.walk_packages(__path__, "testsuite.gateways."):  # type: ignore
    imported = importlib.import_module(module)
    for item in dir(imported):
        if item not in __all__:
            obj = getattr(imported, item)
            if inspect.isclass(obj) and issubclass(obj, AbstractGateway):
                globals()[item] = obj
                __all__.append(item)


def gateway(kind, **kwargs):
    """Return instance of given kind"""
    cls = globals()[kind]
    expected = inspect.signature(cls.__init__).parameters.keys()
    gwargs = {k: v for k, v in kwargs.items() if k in expected}
    return cls(**gwargs)


Gateway = Type[AbstractGateway]
Options = Type[GatewayOptions]

GATEWAYS: Dict[str, Tuple[Gateway, Optional[Gateway], Options]] = {
    "apicast": (SystemApicast, SystemApicast, SystemApicastOptions),
    "apicast-container": (ContainerizedApicast, None, SelfManagedApicastOptions),
    "apicast-selfmanaged": (SelfManagedApicast, SelfManagedApicast, SelfManagedApicastOptions),
    "apicast-operator": (OperatorApicast, OperatorApicast, OperatorApicastOptions),
    "apicast-template": (TemplateApicast, TemplateApicast, TemplateApicastOptions),
    "apicast-tls": (TLSApicast, TLSApicast, TLSApicastOptions),
    "service-mesh": (ServiceMeshGateway, None, ServiceMeshGatewayOptions)
}


class GatewayConfiguration(NamedTuple):
    """Current gateway configuration for use in testsuite, this class is mostly there because of typing"""
    staging: Gateway
    production: Optional[Gateway]
    options: Options


def load_gateway() -> GatewayConfiguration:
    """Gateway that is used to run tests"""
    gateway = settings["threescale"]["gateway"]

    gateway_type = gateway["type"]
    if gateway_type not in GATEWAYS:
        raise ValueError(f"Gateway {gateway_type} is not supported")

    return GatewayConfiguration(*GATEWAYS[gateway_type])


# For this specific use case, I like the lower case names better
configuration = load_gateway()
