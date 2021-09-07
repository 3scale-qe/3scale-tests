"""Tests for importing/exporting product from/to CRD."""

import random
import string
import json
import pytest

from testsuite.config import settings
from testsuite.toolbox import toolbox
from testsuite.utils import blame
from testsuite import rawobj


@pytest.fixture(scope="module")
def export_import_file():
    """Create file for exporting CRD and to import it into dst tenant."""
    file_name = settings['toolbox']['podman_cert_dir'] + '/'
    file_name += ''.join(random.choice(string.ascii_letters) for _ in range(16))

    return file_name


@pytest.fixture(scope="module")
def my_backends_mapping(custom_backend):
    """
    :return: dict in format {path: backend}
    """
    return {'/test1': custom_backend('backend1'), '/test2': custom_backend('backend2')}


@pytest.fixture(scope="module")
def service(my_backends_mapping, custom_service, service_settings, policy_configs):
    """Service fixture"""
    params = service_settings.copy()
    params['name'] += '_export'
    service = custom_service(params, backends=my_backends_mapping)
    service.proxy.list().policies.append(*policy_configs)
    return service


@pytest.fixture(scope="module")
def my_metrics(service, testconfig):
    """Fixture creates metrics for service."""
    proxy = service.proxy.list()

    metric1 = service.metrics.create(rawobj.Metric("metric1"))
    proxy.mapping_rules.create(
        rawobj.Mapping(
            metric1,
            pattern='/test3',
            http_method='GET'))

    metric2 = service.metrics.create(rawobj.Metric("metric2"))
    proxy.mapping_rules.create(
        rawobj.Mapping(
            metric2,
            pattern='/test4',
            http_method='GET'))

    proxy.deploy()

    yield metric1, metric2
    if not testconfig["skip_cleanup"]:
        metric1.delete()
        metric2.delete()


@pytest.fixture(scope="module")
def my_applications(request, service, custom_application, custom_app_plan, my_metrics, lifecycle_hooks):
    "application bound to the account and service existing over whole testing session"
    # pylint: disable=too-many-arguments
    metric1, metric2 = my_metrics
    proxy = service.proxy.list()

    plan_silver = custom_app_plan(
        rawobj.ApplicationPlan(blame(request, "silver")), service)
    plan_silver.limits(metric1).create({
        "metric_id": int(metric1["id"]), "period": "minute", "value": 10})
    plan_silver.limits(metric1).create({
        "metric_id": int(metric1["id"]), "period": "hour", "value": 10})
    plan_silver.pricing_rules(metric1).create({
        "application_plan_id": int(plan_silver["id"]), "metric_id": int(metric1["id"]),
        "min": 10, "max": 100, "cost_per_unit": 1.5})
    plan_silver.pricing_rules(metric1).create({
        "application_plan_id": int(plan_silver["id"]), "metric_id": int(metric1["id"]),
        "min": 101, "max": 200, "cost_per_unit": 3})
    app1 = custom_application(
        rawobj.Application(blame(request, "silver_app"), plan_silver), hooks=lifecycle_hooks)

    plan_gold = custom_app_plan(rawobj.ApplicationPlan(blame(request, "gold")), service)
    plan_gold.limits(metric2).create({
        "metric_id": int(metric2["id"]), "period": "year", "value": 100})
    plan_gold.pricing_rules(metric2).create({
        "application_plan_id": int(plan_gold["id"]), "metric_id": int(metric2["id"]),
        "min": 1, "max": 2, "cost_per_unit": 7})
    app2 = custom_application(rawobj.Application(blame(request, "gold_app"), plan_gold), hooks=lifecycle_hooks)

    proxy.deploy()
    proxy.promote()

    return app1, app2


@pytest.fixture(scope="module")
def export_product(threescale_src1, export_import_file, service, my_backends_mapping, my_metrics, my_applications):
    """Export product from src into file."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    ret = toolbox.run_cmd(f"product export {threescale_src1} {service['id']} -f {export_import_file}")

    assert not ret['stderr']
    assert not ret['stdout']


@pytest.fixture(scope="module")
def import_product(threescale_dst1, export_import_file, export_product, dest_client):
    """Import product from file into dst."""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(f"product import {threescale_dst1} -f {export_import_file}")

    assert not ret['stderr']
    imported_json = json.loads(ret['stdout'])
    dst_prod_id = int(list(imported_json.values())[0]['product_id'])
    dst_product = dest_client.services.read(dst_prod_id)
    return {'stdout': ret['stdout'], 'imported_json': imported_json, 'dst_product': dst_product}


@pytest.fixture(scope="module")
def export_dst_product(threescale_dst1, export_import_file, import_product):
    """Export product from dst into file."""
    export_cmd = f"product export {threescale_dst1} {import_product['dst_product']['id']} "
    export_cmd += f"-f {export_import_file}_exp2"
    ret = toolbox.run_cmd(export_cmd)

    assert not ret['stderr']
    assert not ret['stdout']


def test_compare_two_exports(export_product, export_dst_product, export_import_file):
    """Test compares two exported products."""
    # pylint: disable=unused-argument
    grep_cmd = "grep -E -v '3scale_toolbox_created_at:|name:' "
    output_grep_filename1 = f"{export_import_file}_1"
    input_grep_filename1 = export_import_file
    toolbox.run_cmd(f"{grep_cmd} {input_grep_filename1} > {output_grep_filename1}", False)
    output_grep_filename2 = f"{export_import_file}_2"
    input_grep_filename2 = f"{export_import_file}_exp2"
    toolbox.run_cmd(f"{grep_cmd} {input_grep_filename2} > {output_grep_filename2}", False)
    ret = toolbox.run_cmd(f"diff {output_grep_filename1} {output_grep_filename2}", scale_cmd=False)
    assert list(ret.values()) == ['', '']
