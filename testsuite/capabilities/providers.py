"""This module is where most of the capability providers should be to not have them scattered around"""

from openshift_client import Missing
from weakget import weakget

from testsuite import gateways
from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.config import settings
from testsuite.configuration import openshift


def gateway_capabilities():
    """Adds capabilities provided by gateways"""
    return gateways.default.CAPABILITIES


CapabilityRegistry().register_provider(
    gateway_capabilities,
    {
        Capability.STANDARD_GATEWAY,
        Capability.PRODUCTION_GATEWAY,
        Capability.APICAST,
        Capability.CUSTOM_ENVIRONMENT,
        Capability.JAEGER,
        Capability.SAME_CLUSTER,
        Capability.SERVICE_MESH,
        Capability.SERVICE_MESH_ADAPTER,
        Capability.SERVICE_MESH_WASM,
        Capability.LOGS,
    },
)


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


def fips():
    """
    FIPS cluster limits crypto avaiable to be used
    """

    if openshift().fips:
        return {Capability.FIPS}
    return {Capability.NOFIPS}


CapabilityRegistry().register_provider(fips, {Capability.NOFIPS, Capability.FIPS})


def sso():
    """SSO is available when zync is enabled and RHSSO is configured in dynaconf"""
    enabled = openshift().api_manager.get_path("spec/zync/enabled")
    if enabled is not Missing and not enabled:
        return {}
    if not weakget(settings)["rhsso"]["password"] % None:
        return {}
    return {Capability.SSO}


CapabilityRegistry().register_provider(sso, {Capability.SSO})
