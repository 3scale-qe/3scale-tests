"""Tests for active docs OAS3"""
import json

import importlib_resources as resources
import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.ui.views.admin.audience.developer_portal import ActiveDocsNewView
from testsuite.ui.views.admin.product.active_docs import ActiveDocsDetailView
from testsuite.utils import blame


@pytest.fixture(scope="module")
def service_settings2(request):
    """We need second service settings because service needs to have unique name."""
    return {"name": blame(request, "svc"),
            "backend_version": Service.AUTH_APP_ID_KEY}


@pytest.fixture(scope="module")
def service2(backends_mapping, custom_service, service_settings2, service_proxy_settings, lifecycle_hooks):
    """
    We need second service to test with because we want to test deletion of active docs
    and that needs to be tested on separate service.
    """
    return custom_service(service_settings2, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def active_doc2(request, service2, oas3_body, custom_active_doc):
    """Active doc. bound to second service."""
    return custom_active_doc(rawobj.ActiveDoc(blame(request, "activedoc"), oas3_body, service=service2),
                             autoclean=False)


@pytest.fixture(scope="module")
def oas3_spec():
    """
    OAS3 Active doc spec with 3scale `user key` parameter
    """
    user_key = {
        "name": "user_key",
        "description": "Your access API Key",
        "in": "query",
        "x-data-threescale-name": "user_keys",
        "required": True,
        "schema": {
            "type": "string",
        }
    }
    oas_spec = resources.files("testsuite.resources.oas3").joinpath("petstore-expanded.json").read_text()
    json_spec = json.loads(oas_spec)
    json_spec['paths']['/pets']['get']['parameters'].append(user_key)
    oas_spec = json.dumps(json_spec)
    return oas_spec


@pytest.fixture(scope="module")
def prod_client(prod_client):
    """
    Production client so tests can send request to service production endpoint
    """
    client = prod_client()
    response = client.get('/get')
    assert response.status_code == 200
    return client


# pylint: disable=unused-argument
@pytest.fixture(scope='module')
def ui_active_doc(login, request, navigator, service, oas3_spec):
    """Active doc. bound to service created via UI"""
    name = blame(request, "active_doc_v3")
    system_name = blame(request, "system_name")
    edit = navigator.navigate(ActiveDocsNewView)
    edit.create_spec(name=name,
                     sys_name=system_name,
                     description="Active docs V3",
                     service=service,
                     oas_spec=oas3_spec,
                     publish_option=True)
    return service.active_docs.list()[0]


# pylint: disable=unused-argument, too-many-arguments
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-1460")
def test_active_docs_v3_generate_endpoints(login, navigator, ui_active_doc, service, prod_client, application):
    """
    Test:
        - Create service via API
        - Create Active doc via UI
        - Assert endpoints are correctly generated from oas specification
        - Assert that try endpoint works as expected
    """
    preview_page = navigator.navigate(ActiveDocsDetailView, product=service,
                                      active_doc=ui_active_doc)
    navigator.browser.selenium.refresh()
    preview_page.wait_displayed()
    assert preview_page.oas3.active_docs_section.endpoints == ['/pets', '/pets', '/pets/{id}', '/pets/{id}']
    key = f"{application.entity_name} - {service['name']}"
    preview_page.oas3.make_request("GET", '/pets', key)
    assert preview_page.oas3.active_docs_section.get_response_code() == '200'


def test_active_docs_server(login, navigator, service, active_doc, browser):
    """
    Test:
        - Create service via API
        - Create Active doc via API
        - Assert that Active doc server endpoint is correctly generated
        - Change service production endpoint
        - Assert that Active doc server endpoint is correctly generated
    """
    preview_page = navigator.navigate(ActiveDocsDetailView, product=service,
                                      active_doc=service.active_docs.list()[0])
    preview_page.oas3.server.wait_displayed()
    assert preview_page.oas3.server.read() == service.proxy.list()['endpoint']
    service.proxy.update(params={'endpoint': "https://anything.invalid"})
    service.proxy.deploy()
    browser.refresh()
    preview_page.oas3.server.wait_displayed()
    assert preview_page.oas3.server.read() == service.proxy.list()['endpoint']


def test_active_docs_delete(login, navigator, service2, active_doc2):
    """
    Test:
        - Create service via API
        - Create Active doc via API
        - Delete Active doc via UI
        - Assert that Active doc is deleted
    """
    preview_page = navigator.navigate(ActiveDocsDetailView, product=service2,
                                      active_doc=service2.active_docs.list()[0])
    assert len(service2.active_docs.list()) == 1
    preview_page.delete_btn.click()
    assert len(service2.active_docs.list()) == 0
