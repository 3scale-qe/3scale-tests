"""Test for API key autocomplete in dev portal active docs"""

import importlib_resources as resources
import pytest

from testsuite.ui.views.admin.audience.developer_portal import CMSEditPageView, CMSNewPageView
from testsuite.ui.views.devel import DocsView
from testsuite.utils import blame

PAGE_CONTENT = """
{% content_for javascripts %}
    {{ 'active_docs.js' | javascript_include_tag }}
{% endcontent_for %}

{% assign spec = provider.api_specs['{name}']] %}

<h1>Documentation</h1>

<div class="swagger-section">
  <div id="message-bar" class="swagger-ui-wrap">&nbsp;</div>
  <div id="swagger-ui-container" class="swagger-ui-wrap"></div>
</div>
<script type="text/javascript">
  (function () {
    var url = "{{spec.url}}";
    var serviceEndpoint = "{{spec.api_product_production_public_base_url}}"
    SwaggerUI({ url: url, dom_id: "#swagger-ui-container" }, serviceEndpoint);
  }());
</script>
"""


@pytest.fixture(scope="module")
def oas3_spec():
    """OAS3 Active doc"""
    return resources.files("testsuite.resources.oas3").joinpath("echo-api.json").read_text()


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def api_doc_page(login, navigator, ui_active_doc, request, custom_admin_login):
    """Custom doc page for developer portal"""
    view = navigator.navigate(CMSNewPageView)
    page_name = blame(request, "CustomDocumentation")
    page_path = blame(request, "apidocs")

    view.create(
        page_name,
        ". Root",
        page_path,
        PAGE_CONTENT.replace("{name}", ui_active_doc["system_name"]),
        layout="Main layout",
        liquid_enabled=True,
    )
    page_id = navigator.browser.url.split("/")[-2]

    def cleanup():
        custom_admin_login()
        edit_view = navigator.navigate(CMSEditPageView, page_id=page_id)
        edit_view.delete()

    request.addfinalizer(cleanup)

    view = navigator.new_page(CMSEditPageView, page_id=page_id)
    view.publish()

    return view.get_path()


# pylint: disable=too-many-arguments, unused-argument
def test_api_key_autocomplete(
    prod_client, ui_active_doc, custom_devel_login, application, account, navigator, service, api_doc_page
):
    """
    Setup:
        - Create OAS3 Active doc with API key
    Test:
        - Navigate to dev portal documentations page
        - Try out active doc
        - Assert that API key was autocompleted on selection of application hence status code of request is 200
    """
    custom_devel_login(account)
    view = navigator.open(DocsView, path=api_doc_page)
    key = f"{application.entity_name} - {service['name']}"
    endpoint = view.endpoint("GET", "/")
    endpoint.execute({"user_key": key})
    assert endpoint.status_code == "200"
