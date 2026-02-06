"""
Update api_backend on service without backend configured
"""

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3626"),
]


@pytest.fixture(scope="module")
def service(custom_service, service_settings):
    """
    Create a custom service without backend
    """
    return custom_service(service_settings, proxy_params={}, backends={})


def test_proxy_config(service, private_base_url):
    """
    Test:
        - Update service proxy (add 'api_backend')
        - Assert that service has backend usage
        - Assert that service has one proxy config
        - Delete service backend usage
        - Assert that service hasn't backend usage
        - Update service proxy (change 'auth_user_key')
        - Assert that service still has one proxy config
        - Create service backend usage
        - Assert that service has now two proxy configs
    """
    prev_configs = len(service.proxy.list().configs.list(env="sandbox"))
    service.proxy.list().update({"api_backend": private_base_url("httpbin")})
    usages = service.backend_usages.list()
    assert len(usages) == 1

    usage_id = usages[0]["id"]

    service.backend_usages.delete(usage_id)
    assert len(service.backend_usages.list()) == 0
    configs = service.proxy.list().configs.list(env="sandbox")
    assert len(configs) == prev_configs + 1

    service.proxy.list().update({"auth_user_key": "random_key"})
    configs = service.proxy.list().configs.list(env="sandbox")
    assert len(configs) == prev_configs + 1

    backend_id = usages[0]["backend_id"]
    service.backend_usages.create({"path": "/", "backend_api_id": backend_id})
    service.proxy.deploy()

    configs = service.proxy.list().configs.list(env="sandbox")
    assert len(configs) == prev_configs + 2
