"""
Conftest for connection reuse test
"""

import pytest

from testsuite import rawobj, gateways
from testsuite.openshift.objects import Routes
from testsuite.tests.apicast.policy.tls import embedded


@pytest.fixture(scope="module")
def policy_settings(certificate):
    """
    Embedded upstream mTLS policy
    """
    embedded_cert = embedded(certificate.certificate, "tls.crt", "pkix-cert")
    embedded_key = embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey")
    return rawobj.PolicyConfig(
        "upstream_mtls",
        {
            "certificate_type": "embedded",
            "certificate_key_type": "embedded",
            "certificate": embedded_cert,
            "certificate_key": embedded_key,
        },
    )


@pytest.fixture(scope="session")
def staging_gateway(request, testconfig):
    """
    Standard staging gateway.
    We are testing the communication between the APIcast and API backend,
    the TLS certificates are configured in the backends.
    """
    gateway = gateways.gateway(staging=True)
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


@pytest.fixture(scope="module")
def httpbin_original(custom_httpbin):
    """
    Deployed httpbin with TLS enabled
    """
    return custom_httpbin("hbin-original", tls_route_type=Routes.Types.PASSTHROUGH)


@pytest.fixture(scope="module")
def httpbin_new(custom_httpbin):
    """
    Deployed httpbin with TLS enabled
    """
    return custom_httpbin("hbin-new", tls_route_type=Routes.Types.PASSTHROUGH)


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, httpbin_original, httpbin_new):
    """
    Creates custom backends with paths "/orig", "/new,
    using deployed httpbin_original and httpbin_new as
    the upstream APIs
    """
    return {
        "/orig": custom_backend("backend-orig", httpbin_original),
        "/new": custom_backend("backend-new", httpbin_new),
    }


@pytest.fixture(scope="module")
def backend_usages(service):
    """
    Returns backends bound to the services.
    Should deliver slight performance improvement
    """
    return service.backend_usages.list()


@pytest.fixture(scope="module")
def backend_orig(threescale, backend_usages):
    """
    First bound backend
    Should deliver slight performance improvement
    """
    return threescale.backends.read(backend_usages[0]["backend_id"])


@pytest.fixture(scope="module")
def backend_new(threescale, backend_usages):
    """
    Second bound backend
    Should deliver slight performance improvement
    """
    return threescale.backends.read(backend_usages[1]["backend_id"])


@pytest.fixture(scope="module")
def mapping_rules(service, backend_orig, backend_new):
    """
    Adds the "/" mapping rule to both backends.
    """
    proxy = service.proxy.list()
    proxy.mapping_rules.list()[0].delete()

    orig_metric = backend_orig.metrics.list()[0]
    new_metric = backend_new.metrics.list()[0]
    backend_orig.mapping_rules.create(rawobj.Mapping(orig_metric, "/"))
    backend_new.mapping_rules.create(rawobj.Mapping(new_metric, "/"))
    proxy.deploy()

    return proxy


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Overrides the backend_default from mtls conftest so another httpbin won't be created
    """
    return custom_backend("backend_default", endpoint=private_base_url())
