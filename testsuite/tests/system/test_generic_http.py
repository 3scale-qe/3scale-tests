"""Tests generic HTTP Integration for Zync"""
import backoff
import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.mockserver import Mockserver
from testsuite.utils import blame


pytestmark = pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-2665")


def create_update_matcher(app):
    """Generates a Mockserver matcher for a create/update request"""
    client_id = app["client_id"]
    redirect_url = app["redirect_url"]
    return {
        "path": f"/clients/{client_id}",
        "method": "PUT",
        "body": {
            "type": "JSON",
            "matchType": "STRICT",
            "json": {
                "client_id": client_id,
                "client_secret": "${json-unit.any-string}",
                "client_name": app["name"],
                "redirect_uris": [redirect_url] if redirect_url else [],
                "grant_types": ["authorization_code"],
            },
        },
    }


def delete_matcher(app):
    """Generates a Mockserver matcher for a delete request"""
    return {"path": f"/clients/{app['client_id']}", "method": "DELETE"}


@pytest.fixture(scope="module")
def app2(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Extra app used to test behavior on app delete"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks, autoclean=False)
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def mockserver(private_base_url):
    """Setup generic mockserver"""
    return Mockserver(private_base_url("mockserver"))


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, mockserver):
    """Have application/service with RHSSO auth configured"""

    # pylint: disable=no-self-use
    class _Hook:
        def before_service(self, service_params: dict) -> dict:
            """Update service params"""
            service_params.update(backend_version=Service.AUTH_OIDC)
            return service_params

        # pylint: disable=unused-argument
        def before_proxy(self, _: Service, proxy_params: dict):
            """Update proxy params"""
            proxy_params.update(
                credentials_location="headers",
                oidc_issuer_endpoint=mockserver._url,  # pylint: disable=protected-access
                oidc_issuer_type="rest",
            )
            return proxy_params

    lifecycle_hooks.append(_Hook())


@pytest.fixture(scope="function")
def requests_list(application):
    """
    List of requests that should be received on the mockserver, contains one default value for a default Application
    """
    return [create_update_matcher(application)]


@backoff.on_predicate(backoff.expo, lambda x: not x, max_tries=7, jitter=None)
def resilient_verify_sequence(mockserver, requests_list):
    """Make sure requests to be verified are found even if delayed"""
    return mockserver.verify_sequence(requests_list)


def test_create(requests_list, mockserver):
    """
    Tests that creating an application generates a request
    """
    assert resilient_verify_sequence(mockserver, requests_list)


def test_update(requests_list, mockserver, application):
    """
    Tests that updating any value in application generates a request
    """
    application.update({"description": "test"})
    requests_list.append(create_update_matcher(application))
    application.update({"description": "zuy"})
    requests_list.append(create_update_matcher(application))

    # It takes a bit of time for Zync to reconcile
    assert resilient_verify_sequence(mockserver, requests_list)


def test_update_redirect_url(requests_list, mockserver, application):
    """
    Tests that updating redirect_url in application generates a request with changed redirect_uris
    """
    application.update({"description": "test"})
    requests_list.append(create_update_matcher(application))

    application.update({"redirect_url": "test.com"})
    requests_list.append(create_update_matcher(application))

    # It takes a bit of time for Zync to reconcile
    assert resilient_verify_sequence(mockserver, requests_list)


def test_delete(app2, mockserver):
    """
    Tests that deleting application generates a correct request
    """
    seq = [create_update_matcher(app2)]

    # wait till zync does the job, otherwise it looks like it doesn't bother
    # to do anything for deleted app
    assert resilient_verify_sequence(mockserver, seq)

    app2.update({"description": "zuy"})
    seq.append(create_update_matcher(app2))

    assert resilient_verify_sequence(mockserver, seq)

    app2.delete()
    seq.append(delete_matcher(app2))

    # It takes a bit of time for Zync to reconcile
    assert resilient_verify_sequence(mockserver, seq)
