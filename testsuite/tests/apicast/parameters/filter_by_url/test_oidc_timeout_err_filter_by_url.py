"""
    Regression test for THREESCALE-6139
    Apicast takes long time to startup when using APICAST_SERVICES_FILTER_BY_URL to filter services.
    Problem is that filtered service contains oidc_issuer_enpoint to server
        which will return timeout_err after 1 minute.

    This test recreate this problem using http://example.com:81 url which returns timeout error after 1 minute.


    WARNING: If this service is left undeleted on older versions, it will break self managed apicasts.
"""
from time import time

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest
from threescale_api.resources import Service

from testsuite.capabilities import Capability
from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import blame
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6139")]


@pytest.fixture(scope="module", autouse=True)
def setup(lifecycle_hooks):
    """Setup fixture which adds FakeOIDC lifecycle hook"""
    class FakeOIDC:
        """Fake oidc class which updates services to oidc config with example.com:81 url"""
        # pylint: disable=unused-argument
        @staticmethod
        def before_proxy(service: Service, proxy_params: dict):
            """Update proxy params"""
            proxy_params.update(
                oidc_issuer_endpoint="http://example.com:81",
                oidc_issuer_type="keycloak")
            return proxy_params

        @staticmethod
        def before_service(service_params: dict) -> dict:
            """Update service params"""
            service_params.update(backend_version=Service.AUTH_OIDC)
            return service_params

    lifecycle_hooks.append(FakeOIDC)


@pytest.fixture(scope="module")
def production_gateway(request, configuration):
    """Deploy template apicast gateway."""
    settings_block = {
        "deployments": {
            "production": blame(request, "production")
        }
    }
    options = TemplateApicastOptions(staging=False, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)
    request.addfinalizer(gateway.destroy)
    gateway.create()

    gateway.environ["APICAST_SERVICES_FILTER_BY_URL"] = ".*.doesnt.exist"

    return gateway


# pylint: disable=unused-argument
def test_measure_boot_time(production_gateway, application):
    """
    Measure reload time of the production gateway.
    It shouldn't be more than 60 seconds.

    Apicast should ignore the service with oidc issuer endpoint (http://example.com:81),
    if it doesn't ignore the apicast boot time will be > 60 seconds.
    """
    start_time = time()
    production_gateway.reload()
    end_time = time()
    assert (end_time - start_time) < 60
