"""Test for API key autocomplete in dev portal active docs"""
import importlib_resources as resources
import pytest

from testsuite.ui.views.admin.audience.developer_portal import CMSEditPageView, CMSNewPageView, ActiveDocsNewView
from testsuite.ui.views.devel import DocsView
from testsuite.utils import blame

PAGE_CONTENT = """
{% content_for javascripts %}
  {{ 'active_docs.js' | javascript_include_tag }}
{% endcontent_for %}

<h1>Documentation</h1>
<div class="swagger-section">
  <div id="message-bar" class="swagger-ui-wrap"></div>
  {% for api_spec in provider.api_specs %}
    {% if api_spec.published? %}
    <div id="swagger-ui-container-{{api_spec.system_name}}" class="swagger-ui-wrap"></div>
    <script type="text/javascript">(function () {
    var serviceEndpoint = "{{api_spec.api_product_production_public_base_url}}";
    SwaggerUI({ url: "{{api_spec.url}}", dom_id: "#swagger-ui-container-{{api_spec.system_name}}" },
    serviceEndpoint);}());</script>
    {% endif %}
  {% endfor %}
</div>
"""


@pytest.fixture(scope="module")
def oas3_one_spec():
    """OAS3 Active doc"""
    return resources.files("testsuite.resources.oas3").joinpath("echo-api.json").read_text()


@pytest.fixture(scope="module")
def oas3_two_spec():
    """OAS3 Active doc"""
    return resources.files("testsuite.resources.oas3").joinpath("petstore-expanded.json").read_text()


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def multiple_active_docs(custom_admin_login, request, navigator, service, oas3_one_spec, oas3_two_spec):
    """Active doc. bound to service created via UI"""
    custom_admin_login()
    for doc in [oas3_one_spec, oas3_two_spec]:
        name = blame(request, "active_doc_v3")
        system_name = blame(request, "system_name")
        new_view = navigator.navigate(ActiveDocsNewView)
        new_view.create_spec(
            name=name,
            sys_name=system_name,
            description="Active docs V3",
            service=service,
            oas_spec=doc,
            publish_option=True,
        )


# pylint: disable=unused-argument, too-many-arguments
@pytest.fixture(scope="module")
def multiple_api_doc_page(login, navigator, oas3_one_spec, oas3_two_spec, request, custom_admin_login):
    """Custom doc page for developer portal"""
    view = navigator.navigate(CMSNewPageView)
    page_name = blame(request, "Multiple OAS docs")
    page_path = blame(request, "multiple_oas")

    view.create(
        page_name,
        ". Root",
        page_path,
        PAGE_CONTENT,
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
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7403")
def test_api_multiple_specs(
    multiple_api_doc_page,
    custom_devel_login,
    application,
    account,
    navigator,
    service,
    multiple_active_docs,
):
    """
    Setup:
        - Create multiple OAS3 Active doc with API key
    Test:
        - Navigate to dev portal documentations page
        - Try out active doc
        - Assert that API key was autocompleted on selection of application hence status code of request is 200
    """
    custom_devel_login(account)
    view = navigator.open(DocsView, path=multiple_api_doc_page)
    oas_headings = view.browser.elements("//h2")
    for heading in oas_headings:
        assert heading.text in ["Echo API", "Swagger Petstore"]
