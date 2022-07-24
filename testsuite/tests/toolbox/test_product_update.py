"""Tests for product update Toolbox feature"""

import re

import pytest

from testsuite.toolbox import toolbox
from testsuite.utils import blame, blame_desc
from testsuite import rawobj

pytestmark = pytest.mark.require_version("2.7")


@pytest.fixture(scope="module", params=['product_copy', 'service_copy'])
def product_service(request):
    """Test copying of service or product"""
    return request.param


@pytest.fixture(scope="module")
def my_backends_mapping(custom_backend, product_service):
    """
    :return: dict in format {path: backend}
    """
    if product_service == 'product_copy':
        return {'/test1': custom_backend('backend1'), '/test2': custom_backend('backend2')}
    return {'/test1': custom_backend('backend1')}


@pytest.fixture(scope="module")
def service_settings(request, product_service):
    # pylint: disable=unused-argument
    # it doesn't create new product/service again
    "dict of service settings to be used when service created"
    return {"name": blame(request, "svc")}


@pytest.fixture(scope="module")
def service(testconfig, custom_service, my_backends_mapping, service_settings, policy_configs):
    """Service fixture"""
    service = custom_service(service_settings, backends=my_backends_mapping)
    service.proxy.list().policies.append(*policy_configs)
    yield service
    if not testconfig["skip_cleanup"]:
        for back_usage in service.backend_usages.list():
            back_usage.delete()


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
def my_applications_plans(request, service, custom_application, custom_app_plan, my_metrics, lifecycle_hooks):
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

    return app1, app2, plan_silver, plan_gold


@pytest.fixture(scope="module")
def my_activedoc(request, service, oas3_body, custom_active_doc):
    """This fixture creates active document for service."""
    rawad = rawobj.ActiveDoc(
                name=blame(request, 'activedoc'),
                service=service, body=oas3_body,
                description=blame_desc(request))
    return custom_active_doc(rawad)


@pytest.fixture(scope="module")
def toolbox_copy(service, my_applications_plans, my_activedoc, product_service, threescale_src1, threescale_dst1):
    """Toolbox copies product from one 3scale instance to another one"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    copy_cmd = ''
    if product_service == 'product_copy':
        copy_cmd = 'product copy '
    elif product_service == 'service_copy':
        copy_cmd = 'service copy '
    else:
        copy_cmd = 'copy service '
    copy_cmd += f" -s {threescale_src1} -d {threescale_dst1} {service['id']}"
    ret = toolbox.run_cmd(copy_cmd)
    return (ret['stdout'], ret['stderr'])


@pytest.fixture(scope="module")
def dst_product(toolbox_copy, dest_client):
    """Fixture for destination product."""
    dst_product_id = re.findall(r'new service id (\d+)', toolbox_copy[0])[0]
    return dest_client.services[int(dst_product_id)]


@pytest.fixture(scope="module")
def modify_product(toolbox_copy, service):
    """Modify copied product."""
    # pylint: disable=unused-argument

    # modify origin service
    proxy_inst = service.proxy.list()
    for error in ['error_auth_failed', 'error_auth_missing', 'error_headers_auth_failed',
                  'error_headers_auth_missing', 'error_no_match', 'error_headers_no_match']:
        proxy_inst[error] += '_modified'

    for status in ['error_status_auth_failed', 'error_status_auth_missing',
                   'error_status_no_match']:
        proxy_inst[status] += 100
    proxy_inst.update()


@pytest.fixture(scope="module")
def modify_methods(modify_product, service):
    """ Modify/add methods"""
    # pylint: disable=unused-argument
    hits = service.metrics.read_by_name('hits')
    metodka = hits.methods.create(rawobj.Method('metodka'))
    return [metodka]


@pytest.fixture(scope="module")
def modify_metrics(modify_product, service):
    """ Modify/add/remove metrics/limits"""
    # pylint: disable=unused-argument
    new_metric = service.metrics.create(rawobj.Metric('custom'))
    service.app_plans.list()[0].limits(new_metric).create({
        'metric_id': new_metric['id'], 'period': 'minute', 'value': 10})
    return [new_metric]


@pytest.fixture(scope="module")
def modify_mapping_rules(modify_product, modify_metrics, service, modify_methods):
    """ Modify/delete/add mapping rules"""
    # pylint: disable=unused-argument
    for mapp in service.mapping_rules.list():
        mapp.delete()

    maps = []

    proxy = service.proxy.list()
    hits = service.metrics.read_by_name('hits')

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            modify_metrics[0],
            pattern='/ip',
            http_method='GET')))

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            modify_metrics[0],
            pattern='/anything',
            http_method='POST')))

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            hits,
            pattern='/delete',
            http_method='DELETE')))

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            hits,
            pattern='/put',
            http_method='PUT')))

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            modify_methods[0],
            pattern='/patch',
            http_method='PATCH')))

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            modify_methods[0],
            pattern='/anything',
            http_method='HEAD')))

    maps.append(proxy.mapping_rules.create(
        rawobj.Mapping(
            modify_metrics[0],
            pattern='/anything',
            http_method='OPTIONS')))

    return maps


@pytest.fixture(scope="module")
def modify_apps_account(modify_product, request, custom_application,
                        custom_user, custom_account, testconfig, my_applications_plans):
    """ Modify/delete/add Application plans and Applications and Accounts"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    iname = blame(request, "account")
    acc_raw = rawobj.Account(org_name=iname, monthly_billing_enabled=None, monthly_charging_enabled=None)
    acc_raw.update(dict(name=iname, username=iname, email=f"{iname}@anything.invalid"))
    account_up = custom_account(acc_raw)

    username = blame(request, 'us')
    domain = testconfig["threescale"]["superdomain"]
    usr = dict(username=username, email=f"{username}@{domain}",
               password=blame(request, ''), account_id=account_up['id'])
    custom_user(account_up, params=usr)

    plan_silver = my_applications_plans[2]
    new_application = custom_application(
        rawobj.Application(blame(request, "mega_app"), plan_silver, account=account_up))

    return account_up, new_application


@pytest.fixture(scope="module")
def modify_policies(modify_product, service):
    """ Add new policy"""
    # pylint: disable=unused-argument
    return service.proxy.list().policies.append(
        rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50}))


@pytest.fixture(scope="module")
def modify_activedocs(modify_product, custom_active_doc, request, oas3_body, service, my_activedoc):
    """ Add/modify active docs"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    rawad = rawobj.ActiveDoc(name=blame(request, 'activedoc2'), service=service,
                             body=oas3_body, description=blame_desc(request))
    new_activedoc = custom_active_doc(rawad)
    my_activedoc['description'] += '_updated'
    my_activedoc.update()
    return new_activedoc


@pytest.fixture(scope="module")
def toolbox_update(service, modify_product, product_service, dst_product, modify_methods,
                   modify_metrics, modify_policies, modify_mapping_rules, modify_apps_account,
                   modify_activedocs, threescale_src1, threescale_dst1):
    """Toolbox updates product from one 3scale instance to another one"""
    # 3scale service copy [opts] -s <src> -d <dst> <source-service>
    # [REMOVED] 3scale update service [opts] -s <src> -d <dst> <src_service_id> <dst_service_id>
    # 3scale product copy [opts] -s <source-remote> -d <target-remote> <source-product>
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    update_cmd = ''
    if product_service == 'product_copy':
        update_cmd = 'product copy'
    elif product_service == 'service_copy':
        update_cmd = 'service copy '
    update_cmd += f" -s {threescale_src1} -d {threescale_dst1} {service['id']}"
    ret = toolbox.run_cmd(update_cmd)
    return (ret['stdout'], ret['stderr'])


def test_update(toolbox_update, modify_product, dst_product, product_service, service):
    """Test for checking updated product"""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-arguments
    # pylint: disable=unused-argument
    (stdout, stderr) = toolbox_update

    assert not stderr
    assert re.findall(r'copy proxy policies', stdout)
    assert re.findall(r'copying all service ActiveDocs', stdout)

    service.read()
    dst_product.read()
    if product_service == 'service_copy':
        toolbox.cmp_services(service, dst_product, 'service', False)
    else:
        toolbox.cmp_services(service, dst_product, 'product', False)


def test_backends(toolbox_update, modify_product, service, dest_client, dst_product, product_service):
    """Test backends of the product."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    if product_service == 'service_copy':
        pytest.skip("If copying/updating 'service' one backend is copied/updated in background.")
    stdout = toolbox_update[0]

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


def test_metrics_methods_maps_in_backends(
        toolbox_update, modify_product, service, dest_client, dst_product, product_service):
    """Test metrics, methods and mapping rules for backedn of product"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    if product_service == 'service_copy':
        pytest.skip("If copying/updating 'service' one backend is copied/updated in background.")
    stdout = toolbox_update[0]

    metrics_cnt_txt = sum(map(int, re.findall(r'created (\d+) missing metrics\n', stdout, re.MULTILINE)))
    methods_cnt_txt = sum(map(int, re.findall(r'created (\d+) missing methods\n', stdout, re.MULTILINE)))
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


def test_metrics_methods_maps_in_product(
        toolbox_update, modify_product, service, dest_client, dst_product, modify_metrics,
        my_metrics, modify_mapping_rules):
    """Test metrics, methods and mapping rules of the product"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    stdout = toolbox_update[0]
    service.read()

    assert int(re.findall(r'updated proxy of (\d+) to match the original', stdout)[0]) == int(dst_product['id'])

    src_hits = service.metrics.read_by(**{'friendly_name': 'Hits'})
    (hits_id, number_meth) = re.findall(r'original service hits metric (\d+) has (\d+) methods', stdout)[0]
    assert int(hits_id) == src_hits['id']
    assert int(number_meth) == len(src_hits.methods.list())

    dst_hits = dst_product.metrics.read_by(**{'friendly_name': 'Hits'})
    (dst_hits_id, dst_number_meth) = re.findall(r'target service hits metric (\d+) has (\d+) methods', stdout)[0]
    assert int(dst_hits_id) == dst_hits['id']

    missing = int(re.findall(r'created (\d+) missing methods on target service', stdout)[0])
    assert missing + int(dst_number_meth) == len(dst_hits.methods.list())

    # add Hits metric
    assert int(re.findall(r'original service has (\d+) metrics', stdout)[0]) + 1 == len(service.metrics.list())
    # value from previous copy + hits
    assert int(re.findall(r'target service has (\d+) metrics', stdout)[0]) == len(my_metrics) + 1
    # number of metrics in source product minus precreated Hits metric in target product
    metrs = int(re.findall(r'created (\d+) metrics on the target service', stdout)[0])
    assert metrs == len(modify_metrics)
    # minus method 'metodka' because of; plus hits
    assert len(dst_product.metrics.list()) - 1 == len(modify_metrics) + len(my_metrics) + 1

    maps = re.findall(r'created (\d+) mapping rules\n\ntarget service missing',
                      stdout,
                      re.MULTILINE) \
        or re.findall(r'copying all service ActiveDocs\n\ncreated (\d+) mapping rules',
                      stdout,
                      re.MULTILINE) \
        or re.findall(r'destroying all mapping rules\n\ncreated (\d+) mapping rules',
                      stdout,
                      re.MULTILINE) \
        or re.findall(r'updated proxy of \d+ to match the original\n\ncreated (\d+) mapping rules',
                      stdout,
                      re.MULTILINE)
    assert int(maps[0]) == len(modify_mapping_rules)


def test_app_plans_limits_pricing_rules(
       toolbox_update, modify_product, service, dest_client, dst_product, my_applications_plans, my_metrics):
    """Test app. pland, limits and pricing rules of the product"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    stdout = toolbox_update[0]

    assert int(re.findall(r'target service missing (\d+) application plans', stdout)[0]) == 0

    src_plans = service.app_plans.list()
    dst_plans = dst_product.app_plans.list()
    dst_metrics = dst_product.metrics.list()
    limits_list = \
        re.findall(r'Missing (\d+) plan limits from target application plan (\d+). Source plan (\d+)', stdout)
    for (cnt_limits, dst_plan_id, src_plan_id) in limits_list:
        src_plan = [x for x in src_plans if x['id'] == int(src_plan_id)][0]
        dst_plan = [x for x in dst_plans if x['id'] == int(dst_plan_id)][0]

        # see fixture my_applications_plans

        if (
                src_plan['system_name'].startswith('silver')
                and dst_plan['system_name'].startswith('silver')
        ):
            src_limits = src_plan.limits(my_metrics[0]).list()
            # hits is first
            dst_limits = dst_plan.limits(dst_metrics[1]).list()
            assert int(cnt_limits) == 1
            assert len(src_limits) == len(dst_limits)
        elif (
                src_plan['system_name'].startswith('gold')
                and dst_plan['system_name'].startswith('gold')
        ):
            src_limits = src_plan.limits(my_metrics[1]).list()
            # hits is first
            dst_limits = dst_plan.limits(dst_metrics[2]).list()
            assert int(cnt_limits) == 0
            assert len(src_limits) == len(dst_limits)
        else:
            assert False

    pricing_list = \
        re.findall(r'Missing (\d+) pricing rules from target application plan (\d+). Source plan (\d+)', stdout)
    for (cnt_pricings, dst_plan_id, src_plan_id) in pricing_list:
        src_plan = [x for x in src_plans if x['id'] == int(src_plan_id)][0]
        dst_plan = [x for x in dst_plans if x['id'] == int(dst_plan_id)][0]

        src_prices = src_plan.pricing_rules(my_metrics[0]).list()
        # hits is first
        dst_prices = dst_plan.pricing_rules(dst_metrics[1]).list()
        assert int(cnt_pricings) == 0
        assert len(src_prices) == len(dst_prices)
