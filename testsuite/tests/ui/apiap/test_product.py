"""Rewrite of spec/ui_specs/api_as_a_product/create_service_spec.rb"""

import pytest

from testsuite.ui.views.admin.product.product import ProductEditView
from testsuite.ui.views.admin.product.application import ApplicationPlanDetailView
from testsuite.ui.views.admin.product.integration.settings import ProductSettingsView
from testsuite.ui.views.admin.product.integration.configuration import ProductConfigurationView
from testsuite.ui.views.admin.product.integration.backends import ProductBackendsView, ProductAddBackendView
from testsuite import rawobj, resilient
from testsuite.utils import blame

pytestmark = pytest.mark.usefixtures("login")


@pytest.fixture(scope="module")
def product(request, custom_service):
    """Create custom service that will be deleted during test run"""
    return custom_service({"name": blame(request, "svc")}, autoclean=False)


@pytest.fixture(scope="function")
def service(custom_service, custom_backend, private_base_url, lifecycle_hooks, request):
    """Preconfigured service with backend defined existing over one test run"""
    name = {"name": blame(request, "svc")}
    backend = custom_backend("backend_default", endpoint=private_base_url("echo_api"))
    svc = custom_service(name, backends={"/": backend}, hooks=lifecycle_hooks)
    yield svc
    for usage in svc.backend_usages.list():
        usage.delete()


@pytest.fixture(scope="function")
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app


def test_create_product(custom_ui_product, request):
    """
    Test:
        - Create product via UI
        - Assert that name is correct
        - Assert that system_name is correct
        - Assert that description is correct
    """
    name = blame(request, "name")
    system_name = blame(request, "system_name")
    product = custom_ui_product(name, system_name, "description")
    assert product["name"] == name
    assert product["system_name"] == system_name
    assert product["description"] == "description"


def test_edit_product(navigator, service, threescale):
    """
    Test:
        - Create service via API
        - Edit service via UI
        - Assert that name is correct
        - Assert that description is correct
    """
    edit = navigator.navigate(ProductEditView, product=service)
    edit.update("updated_name", "updated_description")
    product = resilient.resource_read_by_name(threescale.services, service.entity_name)

    assert product["name"] == "updated_name"
    assert product["description"] == "updated_description"


def test_delete_product(navigator, threescale, product):
    """
    Test:
        - Create product via API without autoclean
        - Delete product via UI
        - Assert that deleted product no longer exists
    """
    edit = navigator.navigate(ProductEditView, product=product)
    edit.delete()
    product = threescale.services.read_by_name(product.entity_name)

    assert product is None


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3368")
def test_create_service_without_backend(ui_product):
    """
    Test:
        - Create product via UI
        - Assert that created product doesn't have any backend
    """
    assert len(ui_product.backend_usages.list()) == 0


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3336")
def test_out_of_date_config(service, navigator):
    """
    Test:
        - Create product via API
        - Update product settings
        - Assert that there is notification for out of date configs
    """
    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.update_button.click()
    assert settings.outdated_config.is_displayed


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3576")
def test_update_proxy_url(service, navigator, threescale):
    """
    Test:
        - Create product via API
        - Update product endpoints via UI
        - Assert that product endpoints has changed
    """
    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.update_gateway("https://staging.anything.invalid:443", "https://production.anything.invalid:443")
    product = resilient.resource_read_by_name(threescale.services, service.entity_name)
    proxy = product.proxy.list()

    assert proxy["sandbox_endpoint"] == "https://staging.anything.invalid:443"
    assert proxy["endpoint"] == "https://production.anything.invalid:443"


def test_assign_backend_to_product(navigator, ui_backend, ui_product, threescale):
    """
    Test:
        - Create product via UI
        - Create backend via UI
        - Assign backend to product
        - Assert that backend is assigned correctly
    """
    backend = navigator.navigate(ProductAddBackendView, product=ui_product)
    backend.add_backend(ui_backend, "/get")
    ui_product = resilient.resource_read_by_name(threescale.services, ui_product.entity_name)
    backends = ui_product.backend_usages.list()

    assert len(backends) == 1
    backend_mapping = backends[0]
    assert backend_mapping["path"] == "/get"
    assert backend_mapping["service_id"] == ui_product.entity_id
    assert backend_mapping["backend_id"] == ui_backend.entity_id


def test_remove_backend_from_product(service, navigator, threescale):
    """
    Test:
        - Create product with backend via API
        - Delete backend assignment from product
        - Assert that product has no assigned backends
    """
    backends = navigator.navigate(ProductBackendsView, product=service)
    backend = threescale.backends.read(service.backend_usages.list()[0]["backend_id"])
    backends.remove_backend(backend)
    service = threescale.services.read_by_name(service.entity_name)

    assert len(service.backend_usages.list()) == 0


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3640")
def test_proxy_settings(service, navigator):
    """
    Test:
        - Navigate to Product settings view
        - Assert that staging and production text fields are present
        - Change deployment to self-managed
        - Assert that staging and production text fields are present
        - Change deployment to istio
        - Assert that staging and production text fields are not present
    """
    settings = navigator.navigate(ProductSettingsView, product=service)

    assert settings.staging_url.is_displayed is True
    assert settings.production_url.is_displayed is True

    settings.change_deployment("service_deployment_option_self_managed")
    assert settings.staging_url.is_displayed is True
    assert settings.production_url.is_displayed is True

    settings = navigator.navigate(ProductSettingsView, product=service)
    settings.change_deployment("service_deployment_option_service_mesh_istio")
    assert settings.staging_url.is_enabled is False
    assert settings.production_url.is_enabled is False


# pylint: disable=too-many-arguments
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3373")
@pytest.mark.usefixtures("application")
def test_metrics_hierarchies(service, navigator, threescale, browser):
    """
    Test:
        - Create product and application via API
        - Add product mapping rule with path "/get"
        - Add backend mapping rule with path "/anything"
        - Assert that mapping rules are present at configuration page
        - Assert that metrics are present at application plan detail view
    """
    proxy = service.proxy.list()
    metric = service.metrics.list()[0]
    proxy.mapping_rules.create(rawobj.Mapping(metric, "/get/foo"))

    backend = threescale.backends.read(service.backend_usages.list()[0]["backend_id"])
    metric = backend.metrics.list()[0]
    backend.mapping_rules.create(rawobj.Mapping(metric, "/anything/foo"))

    proxy.update()

    navigator.navigate(ProductConfigurationView, product=service)

    get_path = browser.element(".//*[contains(text(),'/get/foo')]")
    anything_path = browser.element(".//*[contains(text(),'/anything/foo')]")

    assert get_path.is_displayed()
    assert anything_path.is_displayed()

    app_plan = service.app_plans.list()[0]
    plan = navigator.navigate(ApplicationPlanDetailView, product=service, application_plan=app_plan)

    backend_metrics = browser.element(f".//*[contains(text(),'{backend['name']}')]")
    assert next(plan.product_level.rows())
    assert backend_metrics.is_displayed()
