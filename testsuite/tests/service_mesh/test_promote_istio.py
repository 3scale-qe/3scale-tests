"""
Tests that services with istio integration are automatically promoted to production instead of sandbox
"""

import backoff
import pytest

pytestmark = [
    pytest.mark.required_capabilities(),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7424"),
]


@backoff.on_predicate(backoff.fibo, lambda configs: len(configs) > 0, max_tries=8, jitter=None)
def fetch_production_configuration(service):
    """Safely fetches production configuration from 3scale"""
    return service.proxy.list().configs.list(env="production")


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Have service configured with Service Mesh"""
    service_settings.update({"deployment_option": "service_mesh_istio"})
    return service_settings


@pytest.fixture(scope="module")
def service2(backends_mapping, custom_service, service_settings):
    """Custom service, separated from the default one to have better control on the exact parameters"""
    return custom_service(service_settings, {}, backends_mapping, hooks=None)


def test_promote_istio_service(service2):
    """Tests that service has production configuration after config promotion"""
    assert len(fetch_production_configuration(service2)) > 0
