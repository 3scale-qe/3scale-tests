"""
Sets up gateway defined in testsuite settings
"""
from dynaconf import settings
from testsuite.gateways.apicast import SystemApicastGateway, SelfManagedApicastGateway
from testsuite.gateways.containers import ContainerizedApicastGatewayGateway


def load_gateway():
    """Gateway that is used to run tests"""
    global CLASS  # pylint: disable=global-statement
    gateway = settings["threescale"]["gateway"]

    gateway_type = gateway["type"]
    if gateway_type == "apicast":
        staging_gateway = SystemApicastGateway
        production_gateway = staging_gateway
    elif gateway_type == "apicast-container":
        staging_gateway = ContainerizedApicastGatewayGateway
        production_gateway = None
    elif gateway_type == "apicast-selfmanaged":
        staging_gateway = SelfManagedApicastGateway
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
