"""
Sets up gateway defined in testsuite settings
"""
from dynaconf import settings
from testsuite.gateways.apicast import SystemApicast, SelfManagedApicast, OperatorApicast, TemplateApicast, TLSApicast
from testsuite.gateways.containers import ContainerizedApicast

GATEWAYS = {
    "apicast": (SystemApicast, SystemApicast),
    "apicast-container": (ContainerizedApicast, None),
    "apicast-selfmanaged": (SelfManagedApicast, None),
    "apicast-operator": (OperatorApicast, None),
    "apicast-template": (TemplateApicast, TemplateApicast),
    "apicast-tls": (TLSApicast, TLSApicast),
}


def load_gateway():
    """Gateway that is used to run tests"""
    global CLASS  # pylint: disable=global-statement
    gateway = settings["threescale"]["gateway"]

    gateway_type = gateway["type"]
    if gateway_type not in GATEWAYS:
        raise ValueError(f"Gateway {gateway_type} is not supported")

    staging_gateway, production_gateway = GATEWAYS[gateway_type]

    return {
        "staging": staging_gateway,
        "production": production_gateway
    }


CLASSES = load_gateway()
CLASS = CLASSES["staging"]
CAPABILITIES = CLASS.CAPABILITIES
