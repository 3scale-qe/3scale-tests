"""This module is where most of the capability providers should be to not have them scattered around"""
from testsuite import gateways
from testsuite.capabilities import CapabilityRegistry, Capability
from testsuite.configuration import openshift
from testsuite.config import settings


def gateway_capabilities():
    """Adds capabilities provided by gateways"""
    return gateways.default.CAPABILITIES


CapabilityRegistry().register_provider(gateway_capabilities,
                                       {Capability.STANDARD_GATEWAY, Capability.PRODUCTION_GATEWAY, Capability.APICAST,
                                        Capability.CUSTOM_ENVIRONMENT, Capability.JAEGER, Capability.SAME_CLUSTER,
                                        Capability.SERVICE_MESH, Capability.SERVICE_MESH_ADAPTER,
                                        Capability.SERVICE_MESH_WASM, Capability.LOGS})


def ocp_version():
    """
    Adds capabilities for OCP versions,
    This doesnt check server version but only if the 3scale si deployed by APIManager, but for 99% cases it is enough
    """
    if openshift().is_operator_deployment:
        return {Capability.OCP4}
    return {Capability.OCP3}


CapabilityRegistry().register_provider(ocp_version, {Capability.OCP3, Capability.OCP4})


def scaling():
    """
    Scaling is allowed on all known configurations (so far) except for RHOAM
    """
    return {Capability.SCALING} if not settings["threescale"]["deployment_type"] == "rhoam" else {}


CapabilityRegistry().register_provider(scaling, {Capability.SCALING})
