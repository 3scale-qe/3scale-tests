"""Toolbox utils"""

import logging
import os
from io import BytesIO

import jsondiff
import paramiko
import testsuite.toolbox.constants as constants
from testsuite.config import settings


def get_toolbox_cmd(cmd_in):
    """Creates template for Toolbox command according configuration options"""
    if settings['toolbox']['cmd'] == 'rpm':
        return f"3scale {cmd_in}"
    if settings['toolbox']['cmd'] == 'gem':
        return f"scl enable {settings['toolbox']['ruby_version']} '3scale {cmd_in}'"
    if settings['toolbox']['cmd'] == 'podman':
        ret = 'podman run --interactive --rm --privileged=true '
        ret += f"--mount type=bind,src={settings['toolbox']['podman_cert_dir']},"
        ret += f"target={settings['toolbox']['podman_cert_dir']} "
        ret += f"-e SSL_CERT_FILE={settings['toolbox']['podman_cert_dir']}/"
        ret += f"{settings['toolbox']['podman_cert_name']} "
        ret += f"{settings['toolbox']['podman_image']} 3scale "
        if not bool(settings['ssl_verify']):
            ret += '-k '
        ret += f" {cmd_in}"
        return ret
    raise ValueError(f"Unsupported toolbox command: {settings['toolbox']['cmd']}")


def ssh_client():
    """
    Function returns ssh client. Client should be closed!

    @return ssh client
    """
    client = paramiko.client.SSHClient()
    client.load_system_host_keys()
    client.connect(settings['toolbox']['machine_ip'],
                   username=settings['toolbox']['ssh_user'],
                   password=settings['toolbox']['ssh_passwd'])
    return client


def run_cmd(cmd_input, scale_cmd=True):
    """
    Execute command on remote machine

    @param [String] Command to execute
    @return Returns hash with STDOUT and STDERR
    """
    client = ssh_client()
    if isinstance(cmd_input, str):
        cmd_in = [cmd_input]
    else:
        cmd_in = cmd_input

    ret_value = []
    for command in cmd_in:
        logging.debug("Run Toolbox command: '%s'", command)
        if scale_cmd:
            command = get_toolbox_cmd(command)

        _, stdout, stderr = client.exec_command(command)

        stderrstr = os.linesep.join(stderr.readlines())
        stdoutstr = os.linesep.join(stdout.readlines())
        try:
            errno = stdout.channel.recv_exit_status()
            assert errno == 0
        except AssertionError as exc:
            error = f'Errno: {str(errno)}, stderr: {stderrstr}, stdout: {stdoutstr}'
            logging.error(error)
            raise exc

        ret_value.append({'stdout': stdoutstr, 'stderr': stderrstr})

        logging.debug("Output of Toolbox command: stdout: %s; stderr: %s", stdoutstr, stderrstr)
    client.close()

    if isinstance(cmd_input, str):
        return ret_value[0]
    return ret_value


def copy_string_to_remote_file(input_string, remote_file):
    """
    Function copies string into remote file.

    @param [String] Input string
    @param [String] Name of remote file
    """
    client = ssh_client()

    sftp = client.open_sftp()
    sftp.putfo(BytesIO(input_string.encode()), remote_file)

    sftp.close()
    client.close()


def cmp_ents(ent1, ent2, attrlist):
    """
    Function for comparing two entities.

    @param [Object] First entity
    @param [Object] Second entity
    @param [List] List of attributes which should be compared
    """
    for attr in attrlist:
        try:
            assert ent1[attr] == ent2[attr]
        except AssertionError as error:
            logging.error("key:%s, ent1:%s, ent2:%s, error:%s, attrlist:%s",
                          str(attr), str(ent1), str(ent2), str(error), str(attrlist))
            raise error


def find_and_cmp(list1, list2, cmp_function, id_attr=None, cmp_length=True):
    """
    Compare objects in two lists.

    @param [List] First list of entities
    @param [List] Second list of entities
    @param [Function] Function for comparing two entities
    @param [String] Entity ID
    """
    id_attr = id_attr or ['system_name']
    if cmp_length:
        assert len(list1) == len(list2)
    queue = []
    for ent1 in list1:
        for ent2 in list2:
            if all(ent1.entity[r] == ent2.entity[r] for r in id_attr):
                queue.append((ent1, ent2))
                list2.remove(ent2)
                break
    for ent1, ent2 in queue:
        assert len(ent1.keys()) == len(ent2.keys())
        cmp_function(ent1, ent2)


def cmp_services(svc1, svc2, product_service, cmp_length=True):
    """
    Compare two services/products.

    @param [Object] First service
    @param [Object] Second service
    @param [String] Comparing service or product?
    """
    assert len(svc1.entity.keys()) == len(svc2.entity.keys())
    cmp_ents(svc1.entity, svc2.entity, set(svc1.entity.keys()) - constants.SERVICE_CMP_ATTRS)

    cmp_proxies(svc1.proxy.list(), svc2.proxy.list(), product_service)
    cmp_metrics(svc1, svc2, cmp_length)
    cmp_mappings(svc1, svc2, cmp_length)
    cmp_app_plans(svc1, svc2, cmp_length)
    cmp_active_docs(svc1, svc2, cmp_length)
    cmp_backend_usages(svc1, svc2, cmp_length)


def cmp_app_plans(svc1, svc2, cmp_length=True):
    """
    Compare application plans of two services/products.

    @param [Object] First service
    @param [Object] Second service
    @param [Bool] Should we compare lists' length
    """
    app_plan1 = svc1.app_plans.list()
    app_plan2 = svc2.app_plans.list()

    def _cmp_func(ap1, ap2):
        cmp_ents(ap1.entity, ap2.entity, set(ap1.entity.keys()) - constants.APP_PLANS_CMP_ATTRS)
        cmp_pricing_rules(ap1, ap2)
        cmp_limits(ap1, ap2)

    find_and_cmp(app_plan1, app_plan2, _cmp_func, cmp_length=cmp_length)


def cmp_limits(ap1, ap2, cmp_length=True):
    """
    Compare limits of two application plans.

    @param [Object] First list of app. plan
    @param [Object] Second list of app. plan
    @param [Bool] Should we compare lists' length
    """
    def _cmp_func(metr1, metr2):
        find_and_cmp(ap1.limits(metr1).list(),
                     ap2.limits(metr2).list(),
                     lambda lim1, lim2:
                     cmp_ents(lim1.entity, lim2.entity, set(lim1.entity.keys()) - constants.LIMITS_CMP_ATTR),
                     ['period'])

    find_and_cmp(
        ap1.service.metrics.list(),
        ap2.service.metrics.list(),
        _cmp_func,
        ['friendly_name'],
        cmp_length)


def cmp_pricing_rules(ap1, ap2, cmp_length=True):
    """
    Compare pricing rules of two application plans.

    @param [Object] First list of app. plan
    @param [Object] Second list of app. plan
    @param [Bool] Should we compare lists' length
    """
    def _cmp_func(metr1, metr2):
        find_and_cmp(ap1.pricing_rules(metr1).list(),
                     ap2.pricing_rules(metr2).list(),
                     lambda pric1, pric2:
                     cmp_ents(pric1.entity,
                              pric2.entity,
                              set(pric1.entity.keys()) - constants.PRICING_RULES_CMP_ATTRS),
                     ['min', 'max'])

    find_and_cmp(
        ap1.service.metrics.list(),
        ap2.service.metrics.list(),
        _cmp_func,
        ['friendly_name'],
        cmp_length)


def cmp_proxies(proxy1, proxy2, product_service):
    """
    Compare two proxies.

    @param [Object] First proxy
    @param [Object] Second proxy
    """
    assert len(proxy1.entity.keys()) == len(proxy2.entity.keys())
    cmp_ents(proxy1.entity, proxy2.entity, set(proxy1.entity.keys()) - constants.PROXY_CMP_ATTRS)

    assert not jsondiff.diff(proxy1.entity['policies_config'], proxy2.entity['policies_config'])
    assert not jsondiff.diff(proxy1.policies_registry.list(), proxy2.policies_registry.list())

    # do not check 'production' because proxies are not promoted in src and dst
    for env in ['sandbox']:
        last_config1 = proxy1.configs.latest(env)['content']
        last_config2 = proxy2.configs.latest(env)['content']
        assert len(last_config1.keys()) == len(last_config2.keys())
        cmp_ents(last_config1, last_config2, set(last_config1.keys()) - constants.PROXY_CONFIG_CONTENT_CMP_ATTRS)

        last_proxy1 = last_config1['proxy']
        last_proxy2 = last_config2['proxy']
        assert len(last_proxy1.keys()) == len(last_proxy2.keys())
        cmp_attrs = set(last_proxy1.keys()) - constants.PROXY_CONFIG_CONTENT_PROXY_CMP_ATTRS
        if product_service == 'service':
            cmp_attrs.remove('api_backend')
        cmp_ents(last_proxy1, last_proxy2, cmp_attrs)

        # first item is policy inserted by system for backend routing
        if product_service == 'product':
            assert not jsondiff.diff(last_proxy1['policy_chain'][1:], last_proxy2['policy_chain'][1:])
        for rule1, rule2 in zip(last_proxy1['proxy_rules'], last_proxy1['proxy_rules']):
            assert len(rule1.keys()) == len(rule2.keys())
            cmp_ents(rule1, rule2, set(rule1.keys()) - constants.PROXY_RULES_CMP_ATTRS)


def cmp_backends(back1, back2, cmp_length=True):
    """
    Compare two backends.

    @param [Object] First backend
    @param [Object] Second backend
    @param [Bool] Should we compare lists' length
    """
    assert len(back1.entity.keys()) == len(back2.entity.keys())
    cmp_ents(back1.entity, back2.entity, set(back1.entity.keys()) - constants.BACKEND_CMP_ATTRS)
    cmp_metrics(back1, back2, cmp_length)
    cmp_mappings(back1, back2, cmp_length)


def cmp_metrics(ent1, ent2, cmp_length=True):
    """
    Compare metrics of two entities.

    @param [Object] First entity
    @param [Object] Second entity
    @param [Bool] Should we compare lists' length
    """
    metrs1 = ent1.metrics.list()
    metrs2 = ent2.metrics.list()

    def _cmp_func(metr1, metr2):
        cmp_ents(metr1.entity, metr2.entity, set(metr1.keys()) - constants.METRIC_CMP_ATTRS)
        cmp_methods(metr1, metr2, cmp_length)

    find_and_cmp(metrs1, metrs2, _cmp_func, ['friendly_name'], cmp_length)


def cmp_methods(metr1, metr2, cmp_length=True):
    """
    Compare methods of two metrics.

    @param [Object] First metric
    @param [Object] Second metric
    @param [Bool] Should we compare lists' length
    """
    methods1 = metr1.methods.list()
    methods2 = metr2.methods.list()

    def _cmp_func(meth1, meth2):
        cmp_ents(meth1.entity, meth2.entity, set(meth1.keys()) - constants.METRIC_METHOD_CMP_ATTRS)
    find_and_cmp(methods1, methods2, _cmp_func, cmp_length=cmp_length)


def cmp_mappings(ent1, ent2, cmp_length=True):
    """
    Compare mappings of two entities.

    @param [Object] First entity
    @param [Object] Second entity
    @param [Bool] Should we compare lists' length
    """
    maps1 = ent1.mapping_rules.list()
    maps2 = ent2.mapping_rules.list()

    def _cmp_func(map1, map2):
        cmp_ents(map1.entity, map2.entity, set(map1.keys()) - constants.MAPPING_CMP_ATTRS)
    find_and_cmp(maps1, maps2, _cmp_func, ['pattern'], cmp_length)


def cmp_active_docs(svc1, svc2, cmp_length=True):
    """
    Compare active docs of two services.

    @param [Object] First service
    @param [Object] Second service
    @param [Bool] Should we compare lists' length
    """
    acs1 = svc1.active_docs.list()
    acs2 = svc2.active_docs.list()

    def _cmp_func(adc1, adc2):
        cmp_ents(adc1.entity, adc2.entity, set(adc1.keys()) - constants.ACTIVEDOCS_CMP_ATTRS)
    find_and_cmp(acs1, acs2, _cmp_func, cmp_length=cmp_length)


def cmp_backend_usages(svc1, svc2, cmp_length=True):
    """
    Compare backend usages and their subobjects of two services.

    @param [Object] First service
    @param [Object] Second service
    @param [Bool] Should we compare lists' length
    """
    buses1 = svc1.backend_usages.list()
    buses2 = svc2.backend_usages.list()

    def _cmp_func(bus1, bus2):
        cmp_ents(bus1.entity, bus2.entity, set(bus1.keys()) - constants.BACKEND_USAGES_CMP_ATTRS)
        assert bus1['service_id'] == svc1['id']
        assert bus2['service_id'] == svc2['id']
        back1 = svc1.threescale_client.backends.read(bus1['backend_id'])
        back2 = svc2.threescale_client.backends.read(bus2['backend_id'])
        cmp_backends(back1, back2, cmp_length)
    find_and_cmp(buses1, buses2, _cmp_func, ['path'])


def check_object(obj_ent, not_check_list, vals):
    """Check if entity object has values of keys not in 'not_check_list' equal to values 'val'."""
    check_keys = sorted(obj_ent.keys() - not_check_list)
    try:
        assert len(vals) == len(check_keys)
        check_list = zip(check_keys, vals)
        for key, val in check_list:
            assert obj_ent[key] == val
    except AssertionError as error:
        logging.error("object:%s, error:%s, check_keys:%s, obj.keys:%s, vals:%s",
                      str(obj_ent), str(error), str(list(check_keys)),
                      str(list(obj_ent.keys())), str(vals))
        raise error
