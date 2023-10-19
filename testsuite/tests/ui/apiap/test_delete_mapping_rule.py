"""Test for https://issues.redhat.com/browse/THREESCALE-7112"""

import pytest

from testsuite import rawobj
from testsuite.ui.views.admin.product.integration.methods_and_metrics import (
    ProductMethodEditView,
    ProductMethodsView,
    ProductMetricEditView,
    ProductMetricsView,
)

pytestmark = [pytest.mark.usefixtures("login")]


@pytest.fixture(scope="module")
def service(service):
    """Removes default mapping rule from service"""
    service.mapping_rules.delete(service.mapping_rules.list()[0].entity_id)
    service.proxy.deploy()
    return service


@pytest.fixture()
def method(service):
    """Creates method for service"""
    hits = service.metrics.read_by_name("hits")
    method = hits.methods.create(rawobj.Method("method"))
    mapping = service.mapping_rules.create(rawobj.Mapping(method, "/anything"))
    service.proxy.deploy()
    return method, mapping


@pytest.fixture()
def metric(service):
    """Creates metric for service"""
    metric = service.metrics.create(rawobj.Metric("metric"))
    mapping = service.mapping_rules.create(rawobj.Mapping(metric, "/anything"))
    service.proxy.deploy()
    return metric, mapping


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7112")
def test_delete_method_mapping_rule(navigator, service, method):
    """
    Test:
        - Creates method
        - Creates mapping rule for that method
        - Assert that mapping rule is working
        - Assert that method couldn't be deleted because it's used by mapping rule
        - Delete mapping rule
        - Delete method
    """
    method, mapping = method
    view = navigator.navigate(ProductMethodEditView, product=service, method=method)
    view.delete()
    view = navigator.new_page(ProductMethodsView, product=service)
    assert view.notification.is_displayed
    assert view.notification.string_in_flash_message(
        "method is used by the latest gateway configuration and cannot be deleted"
    )

    mapping.delete()
    service.proxy.deploy()

    view = navigator.navigate(ProductMethodEditView, product=service, method=method)
    view.delete()
    view = navigator.new_page(ProductMethodsView, product=service)
    assert view.notification.is_displayed
    assert view.notification.string_in_flash_message("the method was deleted")


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7112")
def test_delete_metric_mapping_rule(navigator, service, metric):
    """
    Test:
        - Creates metric
        - Creates mapping rule for that metric
        - Assert that mapping rule is working
        - Assert that metric couldn't be deleted because it's used by mapping rule
        - Delete mapping rule
        - Delete metric
    """
    metric, mapping = metric
    view = navigator.navigate(ProductMetricEditView, product=service, metric=metric)
    view.delete()
    view = navigator.new_page(ProductMetricsView, product=service)
    assert view.notification.is_displayed
    assert view.notification.string_in_flash_message(
        "metric is used by the latest gateway configuration and cannot be deleted"
    )

    mapping.delete()
    service.proxy.deploy()

    view = navigator.navigate(ProductMetricEditView, product=service, metric=metric)
    view.delete()
    view = navigator.new_page(ProductMetricsView, product=service)
    assert view.notification.is_displayed
    assert view.notification.string_in_flash_message("the metric was deleted")
