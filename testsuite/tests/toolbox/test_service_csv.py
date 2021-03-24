"""Tests for importing service(not product) from CSV Toolbox feature"""

import os
import random
import string
import re
import pytest

from dynaconf import settings
from testsuite.toolbox import toolbox
import testsuite.toolbox.constants as constants
from testsuite.utils import blame


DATA = ['service_name', 'endpoint_name', 'endpoint_http_method', 'endpoint_path',
        'auth_mode', 'endpoint_system_name', 'type']

METHODS = ['GET', 'POST', 'DELETE', 'PUT', 'PATCH', 'HEAD']


@pytest.fixture(scope="module")
def import_data(request):
    """CSV data for import."""

    ret = []
    svc_name = ''
    i = 0
    for method in METHODS:
        rest = i % 3
        if rest == 0:
            svc_name = blame(request, "svc")
        svc_rawobj = [svc_name, svc_name + '_endpoint' + str(rest), method,
                      '/anything/' + svc_name + str(rest), 'api_key', svc_name + str(rest),
                      random.choice(['method', 'metric'])]
        ret.append(dict(zip(DATA, svc_rawobj)))
        i += 1

    return ret


@pytest.fixture(scope="module")
def copy_string_to_remote(import_data):
    """CVS data in one string for importing and copy to remote machine."""
    str_data = ','.join(DATA) + os.linesep
    for line in import_data:
        str_data += ','.join(line.values()) + os.linesep

    fil_name = settings['toolbox']['podman_cert_dir'] + '/'
    fil_name += ''.join(random.choice(string.ascii_letters) for _ in range(16))
    toolbox.copy_string_to_remote_file(str_data, fil_name)

    return fil_name


@pytest.fixture(scope="module")
def import_csv(copy_string_to_remote):
    """Import CSV by Toolbox"""
    import_cmd = f"import csv -d {constants.THREESCALE_DST1} -f "
    import_cmd += copy_string_to_remote
    ret = toolbox.run_cmd(import_cmd)

    assert len(ret['stderr']) == 0

    yield ret['stdout']
    if not settings["skip_cleanup"]:
        toolbox.run_cmd('rm -f ' + copy_string_to_remote, False)


@pytest.fixture(scope="module")
def services(import_csv, dest_client):
    """Return imported services."""
    services_names = re.findall(r'^Service ([\w-]+) has been created.$', import_csv, re.MULTILINE)
    services = {}
    for name in services_names:
        services[name] = dest_client.services.read_by(**{'name': name})
    yield services
    if not settings["skip_cleanup"]:
        for service in services.values():
            if service:
                service.delete()


@pytest.fixture(scope="module")
def metrics(import_csv, services, import_data):
    """Return imported metrics."""
    metric_names = re.findall(r'^Metric ([\w-]+) has been created.$', import_csv, re.MULTILINE)
    metrics = []
    for name in metric_names:
        service = None
        for line in import_data:
            if line['endpoint_name'] == name:
                service = services[line['service_name']]
        metrics.append(service.metrics.read_by(**{'friendly_name': name}))
    yield metrics
    if not settings["skip_cleanup"]:
        for met in metrics:
            if met:
                met.delete()


@pytest.fixture(scope="module")
def methods(import_csv, import_data, services):
    """Return imported methods."""
    method_names = re.findall(r'^Method ([\w-]+) has been created.$', import_csv, re.MULTILINE)
    methods = []
    for name in method_names:
        service = None
        for line in import_data:
            if line['endpoint_name'] == name:
                service = services[line['service_name']]
        hits = service.metrics['hits']
        methods.append(hits.methods.read_by(**{'friendly_name': name}))
    yield methods
    if not settings["skip_cleanup"]:
        for meth in methods:
            if meth:
                meth.delete()


@pytest.fixture(scope="module")
def mapping_rules(import_csv, services):
    """Return imported mapping rules."""
    mapping_names = re.findall(r'^Mapping rule ([\w-]+) has been created.$', import_csv, re.MULTILINE)
    mapping_names = [mapping_names[i:i + 3] for i in range(0, len(mapping_names), 3)]
    mappings = []
    for names, service in zip(mapping_names, services.values()):
        maps = []
        for name in names:
            maps.append(service.mapping_rules.read_by(**{'pattern': '/anything/' + name}))
        mappings.append(maps)
    yield mappings
    if not settings["skip_cleanup"]:
        for mapps in mappings:
            for mapp in mapps:
                if mapp:
                    mapp.delete()


def test_services(import_csv, services):
    """Check imported services."""
    assert int(re.findall(r'^(\d+) services in CSV file$', import_csv, re.MULTILINE)[0]) == len(services)
    assert int(re.findall(r'^(\d+) services have been created$', import_csv, re.MULTILINE)[0]) == len(services)


def test_metrics(import_csv, metrics):
    """Check imported metrics."""
    assert int(re.findall(r'^(\d+) metrics have been created$', import_csv, re.MULTILINE)[0]) == len(metrics)


def test_methods(import_csv, methods):
    """Check imported methods."""
    assert int(re.findall(r'^(\d+) methods have beeen created$', import_csv, re.MULTILINE)[0]) == len(methods)


def test_mapping_rules(import_csv, mapping_rules, services, import_data):
    """Check imported mapping rules."""
    length = 0
    for mapp in mapping_rules:
        length += len(mapp)
    assert int(re.findall(r'^(\d+) mapping rules have been created$', import_csv, re.MULTILINE)[0]) == length

    for mapps, service in zip(mapping_rules, services.keys()):
        for mapp in mapps:
            for line in import_data:
                if line['service_name'] == service and \
                   line['endpoint_http_method'] == mapp['http_method']:
                    assert line['endpoint_path'] == mapp['pattern']
