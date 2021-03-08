"""
Test caching policy policy. Changing caching type to None. Policy remains active but caching is disabled.
https://issues.redhat.com/browse/THREESCALE-4464
"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
              pytest.mark.disruptive,
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4464")]


@pytest.fixture(scope="module")
def service(service):
    """
    Adds policies to services while caching type is set to STRICT mode.
    Promotes the configuration to staging.
    """
    service.proxy.list().policies.append(
        rawobj.PolicyConfig("caching", {"caching_type": "strict"}))
    service.proxy.list().update()
    return service


def test_caching_policy_allow_mod(openshift, api_client, service):
    """
    Tests:
        - if response with valid credentials as before have status_code == 200
        - sets backend-listener to the starting value
        - sets the auth caching policy of an API to None.
        - promotes the configuration to the staging once again.
        - sets replicas of backend listener to 0.
        - the "none" mode disables caching.
            -this mode is useful if you want the policy to remain active, but do not want to use caching.
        - if response with valid credentials as before have status_code == 403
    """
    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    response = api_client().get("/")
    assert response.status_code == 200

    caching_type = service.proxy.list().policies.list()
    caching_type['policies_config'][1]['configuration']['caching_type'] = "none"
    # caching type None is supposed to disable caching, policy remains active, no caching
    caching_type.update()
    # before updating service.proxy.list(), make sure to update caching_type
    service.proxy.list().update(caching_type)
    # promotes the configuration to the staging once again
    openshift.scale("backend-listener", 0)

    try:
        response = api_client().get("/")
        assert response.status_code == 403
    finally:
        openshift.scale("backend-listener", replicas)
