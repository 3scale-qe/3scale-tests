"""This module is where most of the capability providers should be to not have them scattered around"""

from openshift_client import Missing
from weakget import weakget

from testsuite import gateways
from testsuite.capabilities import Capability, CapabilityRegistry
from testsuite.config import settings
from testsuite.configuration import openshift
from testsuite.gateways.apicast.zyncless import ZyncLessApicast


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


def zync_capabilities():
    """Determines zync capabilities based on gateway type and config.

    Case 1 (standard zync): gateway is not ZyncLessApicast and threescale.zync_routes_disabled is not set.
    Provides ZYNC_ROUTES + ZYNC_OIDC_SYNC. Fails fast if APIManager has zync disabled.

    Case 2 (zync without routes): threescale.zync_routes_disabled: true in config.
    Provides only ZYNC_OIDC_SYNC.

    Case 3 (zync disabled): gateway is ZyncLessApicast.
    Provides no zync capabilities. Fails fast if APIManager has zync enabled.
    """
    zync_enabled = openshift().api_manager.get_path("spec/zync/enabled")

    if issubclass(gateways.default, ZyncLessApicast):
        if zync_enabled is Missing or zync_enabled:
            raise RuntimeError("ZyncLessApicast requires zync to be disabled in APIManager (spec.zync.enabled: false)")
        return {}

    if zync_enabled is not Missing and not zync_enabled:
        raise RuntimeError(
            "APIManager has zync disabled. Use ZyncLessApicast gateway or set spec.zync.enabled: true in APIManager."
        )

    zync_routes_disabled = weakget(settings)["threescale"]["zync_routes_disabled"] % False

    if zync_routes_disabled:
        result = openshift().do_action(
            "get",
            [
                "deployment/zync-que",
                "-o=jsonpath={.spec.template.spec.containers[*].env[?(@.name=='DISABLE_K8S_ROUTES_CREATION')].value}",
            ],
            auto_raise=False,
        )
        if result.out().strip() != "1":
            raise RuntimeError(
                "threescale.zync_routes_disabled is set but DISABLE_K8S_ROUTES_CREATION=1 "
                "is not set on the zync-que deployment. "
            )
        return {Capability.ZYNC_OIDC_SYNC}

    return {Capability.ZYNC_ROUTES, Capability.ZYNC_OIDC_SYNC}


CapabilityRegistry().register_provider(zync_capabilities, {Capability.ZYNC_ROUTES, Capability.ZYNC_OIDC_SYNC})
