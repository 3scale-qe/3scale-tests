"""Toolbox utils"""

import logging
import os

from dynaconf import settings
import paramiko

import testsuite.toolbox.constants as constants


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
        ret += f"{settings['toolbox']['podman_image']} 3scale {cmd_in}"
        return ret
    raise ValueError(f"Unsupported toolbox command: {settings['toolbox']['cmd']}")


def run_cmd(cmd_in):
    """
    Execute Toolbox command on remote machine

    @param [String] Command to execute
    @return Returns hash with STDOUT and STDERR
    """
    command = get_toolbox_cmd(cmd_in)
    logging.debug("Run Toolbox command: '%s'", cmd_in)

    client = paramiko.client.SSHClient()
    client.load_system_host_keys()
    client.connect(settings['toolbox']['machine_ip'],
                   username=settings['toolbox']['ssh_user'],
                   password=settings['toolbox']['ssh_passwd'])

    _, stdout, stderr = client.exec_command(command)

    stderr = os.linesep.join(stderr.readlines())
    stdout = os.linesep.join(stdout.readlines())

    logging.debug("Output of Toolbox command: stdout: %s; stderr: %s", stdout, stderr)
    return {'stdout': stdout, 'stderr': stderr}


def cmp_ents(ent1, ent2, attrlist):
    """
    Function for comparing two entities.

    @param [Object] First entity
    @param [Object] Second entity
    @param [List] List of attributes which should be compared
    """
    for attr in attrlist:
        assert ent1[attr] == ent2[attr]


def find_and_cmp(list1, list2, cmp_function, id_attr='system_name'):
    """
    Compare objects in two lists.

    @param [List] First list of entities
    @param [List] Second list of entities
    @param [Function] Function for comparing two entities
    @param [String] Entity ID
    """
    assert len(list1) == len(list2)
    queue = []
    for ent1 in list1:
        for ent2 in list2:
            if ent1.entity[id_attr] == ent2.entity[id_attr]:
                queue.append((ent1, ent2))
                list2.remove(ent2)
                break
    for ent1, ent2 in queue:
        cmp_function(ent1, ent2)


def cmp_backends(back1, back2):
    """
    Compare two backends.

    @param [Object] First backend
    @param [Object] Second backend
    """
    assert len(back1.entity.keys()) == len(back2.entity.keys())
    cmp_ents(back1.entity, back2.entity, set(back1.entity.keys()) - constants.BACKEND_CMP_ATTRS)
    cmp_metrics(back1, back2)
    cmp_mappings(back1, back2)


def cmp_metrics(ent1, ent2):
    """
    Compare two metrics.

    @param [Object] First metric
    @param [Object] Second metric
    """
    metrs1 = ent1.metrics.list()
    metrs2 = ent2.metrics.list()

    def _cmp_func(metr1, metr2):
        cmp_ents(metr1.entity, metr2.entity, set(metr1.keys()) - constants.METRIC_CMP_ATTRS)
        cmp_methods(metr1, metr2)

    find_and_cmp(metrs1, metrs2, _cmp_func, 'friendly_name')


def cmp_methods(metr1, metr2):
    """
    Compare two methods.

    @param [Object] First method
    @param [Object] Second method
    """
    methods1 = metr1.methods.list()
    methods2 = metr2.methods.list()

    def _cmp_func(meth1, meth2):
        cmp_ents(meth1.entity, meth2.entity, set(meth1.keys()) - constants.METRIC_METHOD_CMP_ATTRS)
    find_and_cmp(methods1, methods2, _cmp_func)


def cmp_mappings(ent1, ent2):
    """
    Compare two mappings.

    @param [Object] First mapping
    @param [Object] Second mapping
    """
    maps1 = ent1.mapping_rules.list()
    maps2 = ent2.mapping_rules.list()

    def _cmp_func(map1, map2):
        cmp_ents(map1.entity, map2.entity, set(map1.keys()) - constants.MAPPING_CMP_ATTRS)
    find_and_cmp(maps1, maps2, _cmp_func, 'pattern')
