"""
Sets up gateway defined in testsuite settings
"""
from typing import Tuple, Optional, Dict, Type, NamedTuple

from dynaconf import settings
from testsuite.gateways.apicast import SystemApicast, SelfManagedApicast, OperatorApicast, TemplateApicast, TLSApicast
from testsuite.gateways.apicast.containers import ContainerizedApicast
from testsuite.gateways.gateways import AbstractGateway
from testsuite.gateways.service_mesh import ServiceMeshGateway
from testsuite.gateways.options import GatewayOptions, SystemApicastOptions, SelfManagedApicastOptions, \
    OperatorApicastOptions, TemplateApicastOptions, TLSApicastOptions, ServiceMeshGatewayOptions

Gateway = Type[AbstractGateway]
Options = Type[GatewayOptions]

GATEWAYS: Dict[str, Tuple[Gateway, Optional[Gateway], Options]] = {
    "apicast": (SystemApicast, SystemApicast, SystemApicastOptions),
    "apicast-container": (ContainerizedApicast, None, SelfManagedApicastOptions),
    "apicast-selfmanaged": (SelfManagedApicast, None, SelfManagedApicastOptions),
    "apicast-operator": (OperatorApicast, None, OperatorApicastOptions),
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
configuration = load_gateway()                      # pylint: disable=invalid-name
capabilities = configuration.staging.CAPABILITIES   # pylint: disable=invalid-name
