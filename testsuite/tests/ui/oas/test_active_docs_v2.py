"""Rewrite of spec/ui_specs/api_as_a_product/create_backend_spec.rb.rb"""
from string import Template
from urllib.parse import urlsplit

import pytest
import importlib_resources as resources

from testsuite import rawobj
from testsuite.utils import blame
from testsuite.ui.views.admin.audience.developer_portal import ActiveDocsNewView
from testsuite.ui.views.admin.product.active_docs import ActiveDocsDetailView


@pytest.fixture()
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app


@pytest.mark.usefixtures("login")
def test_active_docs_v2_generate_endpoints(navigator, service, private_base_url, request):
    """
    Test:
        - Create service via API
        - Create Active doc via UI
        - Assert endpoints are correctly generated from oas specification
        - Assert that try endpoint works as expected
    """
    name = blame(request, "active_doc_v2")
    system_name = blame(request, "system_name")
    oas_spec = Template(
        resources.files("testsuite.resources.oas2").joinpath("swagger.json").read_text()
    ).safe_substitute(host=urlsplit(private_base_url()).netloc)
    edit = navigator.navigate(ActiveDocsNewView)
    edit.create_spec(
        name=name,
        sys_name=system_name,
        description="Active docs V2",
        service=service,
        oas_spec=oas_spec,
        publish_option=True,
        skip_validation_option=True,
    )
    preview_page = navigator.navigate(ActiveDocsDetailView, product=service, active_doc=service.active_docs.list()[0])
    preview_page.oas2.expand_operations_link.click()
    assert preview_page.oas2.active_docs_section.endpoints == ["/get", "/post", "/put", "/delete"]
    preview_page.oas2.make_request("/get")
    assert preview_page.oas2.active_docs_section.get_response_code() == "200"
