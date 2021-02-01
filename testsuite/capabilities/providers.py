"""This module is where most of the capability providers should be to not have them scattered around"""
from testsuite.capabilities import CapabilityRegistry
from testsuite.gateways import configuration


def gateway_capabilities():
    """Adds capabilities provided by gateways"""
    staging = configuration.staging.CAPABILITIES
    if configuration.production:
        return staging + configuration.production.CAPABILITIES
    return staging


CapabilityRegistry().register_provider(gateway_capabilities)
