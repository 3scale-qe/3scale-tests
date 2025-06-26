"""Tests wasm authorities filtering"""

from urllib.parse import urlsplit

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.gateways.wasm import ServiceMeshHttpClient
from testsuite.utils import blame

pytestmark = pytest.mark.required_capabilities(Capability.SERVICE_MESH_WASM)


@pytest.fixture(scope="function")
# pylint: disable=too-many-arguments
def custom_extension_and_app(
    custom_service, custom_app_plan, custom_application, lifecycle_hooks, request, staging_gateway
):
    """
    Custom extension with new service, app_plan and application.
    Returns extension and application for use in constructing api_client.
    """
    service = custom_service({"name": blame(request, "svc")}, hooks=lifecycle_hooks)
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "plan")), service=service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    extension = staging_gateway.get_extension(service)
    return extension, app


@pytest.fixture(scope="module")
def get_client_ingress(api_client):
    """Returns getter for api client using default ingress_url as ingress to service mesh."""

    def _get_client(extension, app) -> ServiceMeshHttpClient:
        client: ServiceMeshHttpClient = api_client(app)
        client.root_url = extension.ingress_url  # default, but included for readability
        return client

    return _get_client


@pytest.fixture(scope="module")
def get_client_alias(api_client):
    """Returns getter for api client using service alias url as ingress to service mesh."""

    def _get_client_alias(extension, app) -> ServiceMeshHttpClient:
        client: ServiceMeshHttpClient = api_client(app)
        client.root_url = extension.ingress_alias_url
        return client

    return _get_client_alias


def test_alias(custom_extension_and_app, get_client_ingress, get_client_alias):
    """This test sets extension authorities to only accept alias host."""
    extension, app = custom_extension_and_app
    extension.replace_authorities([urlsplit(extension.ingress_alias_url).netloc])

    assert get_client_ingress(extension, app).get("/").status_code == 403
    assert get_client_alias(extension, app).get("/").status_code == 200


def test_both(custom_extension_and_app, get_client_ingress, get_client_alias):
    """This test sets extension authorities to accept both alias and ingress host."""
    extension, app = custom_extension_and_app
    extension.replace_authorities(
        [urlsplit(extension.ingress_alias_url).netloc, urlsplit(extension.ingress_url).netloc]
    )
    assert get_client_ingress(extension, app).get("/").status_code == 200
    assert get_client_alias(extension, app).get("/").status_code == 200


def test_empty(custom_extension_and_app, get_client_ingress, get_client_alias):
    """This test sets empty extension authorities so no client should succeed."""
    extension, app = custom_extension_and_app
    extension.replace_authorities([])

    assert get_client_ingress(extension, app).get("/").status_code == 403
    assert get_client_alias(extension, app).get("/").status_code == 403


def test_glob_question_mark(custom_extension_and_app, get_client_ingress, get_client_alias):
    """
    This test checks glob functionality in authorities string.
    Test sets url with replaced '.' character with '?' that denotes _any just one_
    Only authority host is the edited one.
    """
    extension, app = custom_extension_and_app

    url = urlsplit(extension.ingress_url).netloc
    url = url.replace(".", "?")

    extension.replace_authorities([url])
    assert get_client_ingress(extension, app).get("/").status_code == 200
    assert get_client_alias(extension, app).get("/").status_code == 403


@pytest.mark.parametrize("glob", ["*", "?+"])
def test_glob_star_plus(custom_extension_and_app, get_client_ingress, get_client_alias, glob):
    """
    This test checks glob functionality in authorities string.
    First test checks that clients connect when last subdomain is changed to '*'
    Second test checks the same with '?+' that is equivalent to '*'
    Only authority host is the edited one.
    """
    extension, app = custom_extension_and_app

    url = urlsplit(extension.ingress_url).netloc.split(".")
    url[0] = glob

    extension.replace_authorities([".".join(url)])
    assert get_client_ingress(extension, app).get("/").status_code == 200
    assert get_client_alias(extension, app).get("/").status_code == 200
