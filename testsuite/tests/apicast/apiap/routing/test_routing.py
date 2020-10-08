"""
Test that request to product with specific paths to backends will be routed to correct backend
"""
import pytest
from pytest_cases import fixture_plus, parametrize_with_cases
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest
from testsuite.tests.apicast.apiap.routing import routing_cases
from testsuite.utils import blame
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.8.2')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4937")]


@fixture_plus
def service(backends_mapping, service_proxy_settings, custom_service, request, lifecycle_hooks):
    """Service configured with all backends that are connected via each path from paths"""
    return custom_service({"name": blame(request, "svc")},
                          service_proxy_settings,
                          backends_mapping,
                          hooks=lifecycle_hooks)


@fixture_plus
@parametrize_with_cases("case_data", cases=routing_cases)
def paths(case_data):
    """Array of paths that are used for backend usages (for each path connect product with new backend)"""
    return case_data


@fixture_plus
def backends_mapping(custom_backend, paths, private_base_url):
    """
    Backend mapping for each path is created new backend
    Backend url is created with suffix "/anything{i}", where i is index of path in array paths
        in order to test that request was routed to correct backend
    """
    mappings = {}
    for i, path in enumerate(paths):
        url = private_base_url() + f"/anything/{i}"
        mappings.update({path: custom_backend(endpoint=url)})
    return mappings


@fixture_plus
def application(service, custom_app_plan, custom_application, lifecycle_hooks, request):
    """application bound to the account and service"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


def test(application, paths):
    """
    Test that  for each path from paths, the request will be routed to correct backend.
    Each backend is connected to product via 'path' and has url that has suffix "/anything{i}"
        in order to know that it was routed to correct backend
    :param application: application
    :param paths: array of used paths
    """
    for i, path in enumerate(paths):
        response = application.api_client().get(f"{path}")
        assert response.status_code == 200, f"Path {path} was not mapped to any backend"

        echoed_request = EchoedRequest.create(response)
        assert echoed_request.path == f"/anything/{i}/", f"Path {path} was routed incorrectly"
