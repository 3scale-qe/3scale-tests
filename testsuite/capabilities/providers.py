"""This module is where most of the capability providers should be to not have them scattered around"""
from testsuite import CONFIGURATION
from testsuite.capabilities import CapabilityRegistry, Capability
from testsuite.gateways import configuration


def _rhoam():
    """Returns True, if the current instance is RHOAM. Detects RHOAM by annotations on APIManager object"""
    client = CONFIGURATION.openshift()
    if client.is_operator_deployment:
        manager = client.api_manager
        if manager.get_annotation("integreatly-name") or manager.get_annotation("integreatly-namespace"):
            return True

    return False


def gateway_capabilities():
    """Adds capabilities provided by gateways"""
    staging = configuration.staging.CAPABILITIES
    if configuration.production:
        return staging + configuration.production.CAPABILITIES
    return staging


CapabilityRegistry().register_provider(gateway_capabilities)


def ocp_version():
    """
    Adds capabilities for OCP versions,
    This doesnt check server version but only if the 3scale si deployed by APIManager, but for 99% cases it is enough
    """
    if CONFIGURATION.openshift().is_operator_deployment:
        return {Capability.OCP4}
    return {Capability.OCP3}


CapabilityRegistry().register_provider(ocp_version)


def scaling():
    """
    Scaling is allowed on all known configurations (so far) except for RHOAM
    """
    return {Capability.SCALING} if not _rhoam() else {}


CapabilityRegistry().register_provider(scaling)
