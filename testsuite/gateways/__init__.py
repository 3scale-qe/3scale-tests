"""
Sets up gateway defined in testsuite settings
"""
from dynaconf import settings
from testsuite.gateways.apicast import SystemApicast, SelfManagedApicast
from testsuite.gateways.containers import ContainerizedApicast


def load_gateway():
    """Gateway that is used to run tests"""
    global CLASS  # pylint: disable=global-statement
    gateway = settings["threescale"]["gateway"]

    gateway_type = gateway["type"]
    if gateway_type == "apicast":
        staging_gateway = SystemApicast
        production_gateway = staging_gateway
    elif gateway_type == "apicast-container":
        staging_gateway = ContainerizedApicast
        production_gateway = None
    elif gateway_type == "apicast-selfmanaged":
        staging_gateway = SelfManagedApicast
        production_gateway = None
    else:
        raise ValueError(f"Gateway {gateway_type} is not supported")

    return {
        "staging": staging_gateway,
        "production": production_gateway
    }


CLASSES = load_gateway()
CLASS = CLASSES["staging"]
CAPABILITIES = CLASS.CAPABILITIES
