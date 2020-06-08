"""Tests for product copy Toolbox feature"""

import re

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

import testsuite.toolbox.constants as constants
from testsuite.toolbox import toolbox
from testsuite.utils import blame, blame_desc
from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.7')")


@pytest.fixture(scope="module")
def my_policy_configs():
    """Configuration of most of the available policies."""
    return [
        rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50}),
        rawobj.PolicyConfig("caching", {"caching_type": "allow"}),
        rawobj.PolicyConfig("content_caching", {"rules": [
            {"cache": True, "header": "X-Cache-Status", "condition": {
                "combine_op": "and", "operations": [
                    {"left": "oo", "op": "==", "right": "oo"}
                ]
            }}]}),
        rawobj.PolicyConfig("headers", {
            "response": [{"op": "add", "header": "X-RESPONSE-CUSTOM-ADD", "value_type": "plain",
                          "value": "Additional response header"}],
            "request": [{"op": "add", "header": "X-REQUEST-CUSTOM-ADD", "value_type": "plain",
                         "value": "Additional request header"}],
            "enable": True}),
        rawobj.PolicyConfig("ip_check", {
            "check-type": "whitelist",
            "client_ip_sources": ["X-Forwarded-For"],
            "ips_list": ['0.0.0.0']
            }),
        rawobj.PolicyConfig("jwt_claim_check", {
            "rules": [
                {
                    "methods": ['GET'],
                    "operations": [{
                        "op": "==",
                        "jwt_claim": "azp",
                        "value": "client_id",
                        "value_type": "plain",
                        "jwt_claim_type": "plain",
                        }],
                    "combine_op": "and",
                    "resource": "/get",
                    "resource_type": "plain",
                    }
                ],
            "error_message": "error message",
            }),
        rawobj.PolicyConfig("retry", {"retries": 5}),
        rawobj.PolicyConfig("routing", {"rules": [
            {"url": "http://url1.org", "condition": {"operations": [
                {"op": "==", "value": "/anything/anything", "match": "path"}]},
             "replace_path": "{{ original_request.path | remove_first: '/anything' }}"}]}),
        rawobj.PolicyConfig("soap", {
            "mapping_rules": [{"pattern": "soap_policy_action", "metric_system_name": "hits", "delta": "3"},
                              {"pattern": "soap_policy_ctype", "metric_system_name": "hits", "delta": "5"}]}),
        rawobj.PolicyConfig("cors", {
            "allow_methods": ["GET", "POST"], "allow_credentials": True, "allow_origin": "localhost"}),
        rawobj.PolicyConfig("liquid_context_debug", {}),
        rawobj.PolicyConfig("default_credentials", {
            "auth_type": "user_key", "user_key": "sdfsdfsofhsdkfjhjksdhf"}),
        rawobj.PolicyConfig("headers", {
            "response": [{"op": "set", "header": "X-RESPONSE-CUSTOM-SET", "value_type": "plain",
                          "value": "Response set header"}],
            "request": [{"op": "set", "header": "X-REQUEST-CUSTOM-SET", "value_type": "plain",
                         "value": "Request set header"}]}),
        rawobj.PolicyConfig("maintenance_mode", {
            "message_content_type": "text/plain; charset=utf-8",
            "status": 328, "message": "Service Unavailable - Maintenance"}),
        rawobj.PolicyConfig("rewrite_url_captures", {"transformations": [
            {"match_rule": "/{var_1}/{var_2}", "template": "/{var_2}?my_arg={var_1}"},
            {"match_rule": "/{var_1}/{var_2}", "template": "/my_arg={var_2}?my_arg2={var_1}"}]}),
        rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5}),
        rawobj.PolicyConfig("url_rewriting", {"commands": [{"op": "gsub", "regex": "hello", "replace": "get"}]}),
        ]


@pytest.fixture(scope="module", params=['service', 'product'])
def product_service(request):
    """Test copying of service or product"""
    return request.param


@pytest.fixture(scope="module")
def my_backends_mapping(custom_backend, product_service):
    """
    :return: dict in format {path: backend}
    """
    if product_service == 'product':
        return {'/test1': custom_backend('backend1'), '/test2': custom_backend('backend2')}
    return {'/test1': custom_backend('backend1')}


@pytest.fixture(scope="module")
def service_settings(request, product_service):
    # pylint: disable=unused-argument
    # it doesn't create new product/service again
    "dict of service settings to be used when service created"
    return {"name": blame(request, "svc")}


@pytest.fixture(scope="module")
def service(custom_service, my_backends_mapping, service_settings, my_policy_configs):
    """Service fixture"""
    service = custom_service(service_settings, backends=my_backends_mapping)
    service.proxy.list().policies.append(*my_policy_configs)
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

    proxy.update()

    yield metric1, metric2
    if not testconfig["skip_cleanup"]:
        metric1.delete()
        metric2.delete()


@pytest.fixture(scope="module")
def my_applications(request, service, custom_application, custom_app_plan, my_metrics, lifecycle_hooks,
                    product_service, private_base_url):
    "application bound to the account and service existing over whole testing session"
    # pylint: disable=too-many-arguments
    # pylint: disable=unused-argument
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

    proxy.update()
    proxy.promote()

    return app1, app2


@pytest.fixture(scope="module")
def my_activedoc(request, service, oas3_body, custom_active_doc):
    """This fixture creates active document for service."""
    rawad = rawobj.ActiveDoc(
                name=blame(request, 'activedoc'),
                service=service, body=oas3_body,
                description=blame_desc(request))
    return custom_active_doc(rawad)


@pytest.fixture(scope="module")
def toolbox_copy(service, my_applications, my_activedoc, product_service):
    """Toolbox copies product from one 3scale instance to another one"""
    # pylint: disable=unused-argument
    copy_cmd = ''
    if product_service == 'product':
        copy_cmd = 'product '
    else:
        copy_cmd = 'service '
    copy_cmd += f"copy -s {constants.THREESCALE_SRC1} -d {constants.THREESCALE_DST1} {service['id']}"
    ret = toolbox.run_cmd(copy_cmd)
    return (ret['stdout'], ret['stderr'])


@pytest.fixture(scope="module")
def dst_product(toolbox_copy, dest_client):
    """Fixture for destination product."""
    dst_product_id = re.findall(r'new service id (\d+)', toolbox_copy[0])[0]
    return dest_client.services[int(dst_product_id)]


@pytest.mark.toolbox
def test_copy(toolbox_copy, service, my_applications, my_activedoc, dest_client,
              my_metrics, dst_product, product_service):
    """Test for checking copied product"""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-arguments
    # pylint: disable=unused-argument
    (stdout, stderr) = toolbox_copy

    assert not stderr
    assert re.findall(r'copy proxy policies', stdout)
    assert re.findall(r'copying all service ActiveDocs', stdout)

    toolbox.cmp_services(service, dst_product, product_service)


@pytest.mark.toolbox
def test_backends(toolbox_copy, service, my_applications, my_activedoc, dest_client,
                  my_metrics, dst_product, product_service):
    """Test backends of the product."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    if product_service == 'service':
        pytest.skip("If copying 'service' one backend is copied in background.")

    stdout = toolbox_copy[0]

    my_service_backend_usages_list = service.backend_usages.list()
    src_backends = {
        int(idc): sysn for (idc, sysn) in
        re.findall(r'source backend ID: (\d+) system_name: (\w+)', stdout)
    }
    for back_use in my_service_backend_usages_list:
        assert int(back_use['backend_id']) in [int(x) for x in list(src_backends.keys())]
        assert back_use.backend['system_name'] == src_backends[int(back_use['backend_id'])]

    dst_backends = {
        int(idc): sysn for (idc, sysn) in
        re.findall(r'target backend ID: (\d+) system_name: (\w+)', stdout)
    }
    for back_use in dst_product.backend_usages.list():
        assert int(back_use['backend_id']) in dst_backends.keys()
        assert back_use.backend['system_name'] == dst_backends[int(back_use['backend_id'])]

    assert int(re.findall(r'created/upated (\d+) backends', stdout)[0]) == len(dst_product.backend_usages.list())


@pytest.mark.toolbox
def test_metrics_methods_maps_in_backends(
        toolbox_copy, service, my_applications, my_activedoc, dest_client,
        my_metrics, dst_product):
    """Test metrics, methods and mapping rules for backedn of product"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    stdout = toolbox_copy[0]

    metrics_cnt_txt = sum(map(int, re.findall(r'created (\d+) missing metrics', stdout)))
    methods_cnt_txt = sum(map(int, re.findall(r'created (\d+) missing methods', stdout)))
    maps_cnt_txt = sum(map(int, re.findall(r'missing methods\n\ncreated (\d+) mapping rules', stdout, re.MULTILINE)))

    metrics_cnt = 0
    methods_cnt = 0
    maps_cnt = 0
    my_service_backend_usages_list = service.backend_usages.list()
    for busage in my_service_backend_usages_list:
        back = busage.backend
        # minus Hits in all backends
        metrics_cnt += len(back.metrics.list()) - 1

        hits = back.metrics.read_by(**{'friendly_name': 'Hits'})
        methods_cnt += len(hits.methods.list())

        maps_cnt += len(back.mapping_rules.list())

    assert metrics_cnt_txt == metrics_cnt
    assert methods_cnt_txt == methods_cnt
    assert maps_cnt_txt == maps_cnt


@pytest.mark.toolbox
def test_metrics_methods_maps_in_product(
        toolbox_copy, service, my_applications, my_activedoc, dest_client,
        my_metrics, dst_product):
    """Test metrics, methods and mapping rules of the product"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    stdout = toolbox_copy[0]

    assert int(re.findall(r'updated proxy of (\d+) to match the original', stdout)[0]) == int(dst_product['id'])

    src_hits = service.metrics.read_by(**{'friendly_name': 'Hits'})
    (hits_id, number_meth) = re.findall(r'original service hits metric (\d+) has (\d+) methods', stdout)[0]
    assert int(hits_id) == src_hits['id']
    assert int(number_meth) == len(src_hits.methods.list())

    dst_hits = dst_product.metrics.read_by(**{'friendly_name': 'Hits'})
    (dst_hits_id, dst_number_meth) = re.findall(r'target service hits metric (\d+) has (\d+) methods', stdout)[0]
    assert int(dst_hits_id) == dst_hits['id']
    assert int(dst_number_meth) == len(dst_hits.methods.list())

    missing = int(re.findall(r'created (\d+) missing methods on target service', stdout)[0])
    assert missing == len(dst_hits.methods.list())

    assert int(re.findall(r'original service has (\d+) metrics', stdout)[0]) == len(service.metrics.list())
    # target product has precreated metric Hits
    assert int(re.findall(r'target service has (\d+) metrics', stdout)[0]) == 1
    # number of metrics in source product minus precreated Hits metric in target product
    metrs = int(re.findall(r'created (\d+) metrics on the target service', stdout)[0])
    assert metrs == len(dst_product.metrics.list()) - 1

    assert int(re.findall(r'destroying all mapping rules\n\ncreated (\d+) mapping rules',
                          stdout, re.MULTILINE)[0]) == len(dst_product.mapping_rules.list())


@pytest.mark.toolbox
def test_app_plans_limits_pricing_rules(
        toolbox_copy, service, my_applications, my_activedoc, dest_client,
        my_metrics, dst_product):
    """Test app. pland, limits and pricing rules of the product"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    stdout = toolbox_copy[0]

    assert int(re.findall(r'target service missing (\d+) application plans', stdout)[0]) == len(my_applications)

    src_plans = service.app_plans.list()
    dst_plans = dst_product.app_plans.list()
    dst_metrics = dst_product.metrics.list()
    limits_list = \
        re.findall(r'Missing (\d+) plan limits from target application plan (\d+). Source plan (\d+)', stdout)
    for (cnt_limits, dst_plan_id, src_plan_id) in limits_list:
        src_plan = [x for x in src_plans if x['id'] == int(src_plan_id)][0]
        dst_plan = [x for x in dst_plans if x['id'] == int(dst_plan_id)][0]

        # see fixture my_applications

        if (
                src_plan['system_name'].startswith('silver')
                and dst_plan['system_name'].startswith('silver')
        ):
            src_limits = src_plan.limits(my_metrics[0]).list()
            # hits is first
            dst_limits = dst_plan.limits(dst_metrics[1]).list()
            assert len(src_limits) == int(cnt_limits)
            assert len(dst_limits) == int(cnt_limits)
        elif (
                src_plan['system_name'].startswith('gold')
                and dst_plan['system_name'].startswith('gold')
        ):
            src_limits = src_plan.limits(my_metrics[1]).list()
            # hits is first
            dst_limits = dst_plan.limits(dst_metrics[2]).list()
            assert len(src_limits) == int(cnt_limits)
            assert len(dst_limits) == int(cnt_limits)
        else:
            assert False

    pricing_list = \
        re.findall(r'Missing (\d+) pricing rules from target application plan (\d+). Source plan (\d+)', stdout)
    for (cnt_pricings, dst_plan_id, src_plan_id) in pricing_list:
        src_plan = [x for x in src_plans if x['id'] == int(src_plan_id)][0]
        dst_plan = [x for x in dst_plans if x['id'] == int(dst_plan_id)][0]

        if (
                src_plan['system_name'].startswith('silver')
                and dst_plan['system_name'].startswith('silver')
        ):
            src_prices = src_plan.pricing_rules(my_metrics[0]).list()
            # hits is first
            dst_prices = dst_plan.pricing_rules(dst_metrics[1]).list()
            assert len(src_prices) == int(cnt_pricings)
            assert len(dst_prices) == int(cnt_pricings)
        elif (
                src_plan['system_name'].startswith('gold')
                and dst_plan['system_name'].startswith('gold')
        ):
            src_prices = src_plan.pricing_rules(my_metrics[1]).list()
            # hits is first
            dst_prices = dst_plan.pricing_rules(dst_metrics[2]).list()
            assert len(src_prices) == int(cnt_pricings)
            assert len(dst_prices) == int(cnt_pricings)
        else:
            assert False
