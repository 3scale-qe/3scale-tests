"""Tests generic HTTP Integration for Zync"""
import time

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
def new_application(
    custom_app_plan, custom_application, service, request, lifecycle_hooks
):
    """Custom application fixture than also handles app_plan"""

    def _app(app_name):
        plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
        app = custom_application(
            rawobj.Application(blame(request, app_name), plan),
            hooks=lifecycle_hooks,
            autoclean=False,
        )
        service.proxy.deploy()
        return app

    return _app


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


def test_create(requests_list, mockserver):
    """
    Tests that creating an application generates a request
    """
    assert mockserver.verify_sequence(requests_list)


def test_update(requests_list, mockserver, application):
    """
    Tests that updating any value in application generates a request
    """
    application.update({"description": "test"})
    requests_list.append(create_update_matcher(application))
    application.update({"description": "zuy"})
    requests_list.append(create_update_matcher(application))

    # It takes a bit of time for Zync to reconcile
    time.sleep(2)
    assert mockserver.verify_sequence(requests_list)


def test_update_redirect_url(requests_list, mockserver, application):
    """
    Tests that updating redirect_url in application generates a request with changed redirect_uris
    """
    application.update({"description": "test"})
    requests_list.append(create_update_matcher(application))

    application.update({"redirect_url": "test.com"})
    requests_list.append(create_update_matcher(application))

    # It takes a bit of time for Zync to reconcile
    time.sleep(2)
    assert mockserver.verify_sequence(requests_list)


def test_delete(requests_list, mockserver, new_application):
    """
    Tests that deleting application generates a correct request
    """
    application = new_application("app2")
    requests_list.append(create_update_matcher(application))

    application.update({"description": "zuy"})
    requests_list.append(create_update_matcher(application))

    application.delete()
    requests_list.append(delete_matcher(application))

    # It takes a bit of time for Zync to reconcile
    time.sleep(2)
    assert mockserver.verify_sequence(requests_list)
