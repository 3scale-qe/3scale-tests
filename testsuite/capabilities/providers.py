"""This module is where most of the capability providers should be to not have them scattered around"""
from testsuite import CONFIGURATION
from testsuite.capabilities import CapabilityRegistry, Capability
from testsuite.gateways import configuration


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
