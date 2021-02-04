"""Tests for importing OAS3 by Toolbox"""

import re

import pytest
import yaml
from testsuite.config import settings

import testsuite.toolbox.constants as constants
from testsuite.toolbox import toolbox


OAS3_FILE = 'testsuite/resources/oas3/petstore-expanded.yaml'
USER_KEY = '123456'


@pytest.fixture(scope="module")
def petstore_yaml(fil=OAS3_FILE):
    """Loads yaml file"""
    return yaml.load(open(fil, 'r'), Loader=yaml.SafeLoader)


@pytest.fixture(scope="module")
def import_oas3(dest_client):
    """Import OAS3 by Toolbox"""
    import_cmd = f"import openapi -d {constants.THREESCALE_DST1} {settings['toolbox']['podman_cert_dir']}"
    import_cmd += f"/petstore-expanded.yaml --default-credentials-userkey={USER_KEY}"
    ret = toolbox.run_cmd(import_cmd)
    (_, service_id, service_name) = re.findall(
        r'^(Created|Updated) service id: (\d+), name: (.+)$', ret['stdout'], re.MULTILINE)[0]
    service = dest_client.services[int(service_id)]
    yield (ret, service_id, service_name, service)
    if not settings["skip_cleanup"]:
        service.delete()


def test_import(import_oas3, petstore_yaml):
    """Checks import results"""
    (ret, service_id, service_name, service) = import_oas3
    assert not ret['stderr']
    assert int(service_id) == int(service['id'])
    assert petstore_yaml['info']['title'] == service_name
    assert re.findall(r'^Service proxy updated$', ret['stdout'], re.MULTILINE)
    assert re.findall(r'^destroying all mapping rules$', ret['stdout'], re.MULTILINE)
    for path in petstore_yaml['paths'].keys():
        for method in petstore_yaml['paths'][path].keys():
            path_url = f"/{petstore_yaml['servers'][0]['url'].split('/')[-1]}{path}"
            assert re.findall(
                rf"^Created {method.upper()} {path_url}\$ endpoint$",
                ret['stdout'],
                re.MULTILINE)
    assert re.findall(r'^Service policies updated$', ret['stdout'], re.MULTILINE)


def test_service(import_oas3, petstore_yaml):
    """Checks importes service"""
    service = import_oas3[3]
    assert service['description'] == petstore_yaml['info']['description']
    assert service['name'] == petstore_yaml['info']['title']


def test_metrics_mappings(import_oas3, petstore_yaml):
    """Checks imported metrics"""
    # pylint: disable=too-many-nested-blocks
    service = import_oas3[3]
    metrics = service.metrics.list()
    mappings = service.proxy.list().mapping_rules.list()
    pet_number = 0
    for path in petstore_yaml['paths'].keys():
        for method in petstore_yaml['paths'][path].keys():
            pet = petstore_yaml['paths'][path][method]
            name = pet['operationId']
            for met in metrics:
                if met['friendly_name'] == name:
                    pet_number += 1
                    assert pet['description'] == met['description']
                    for mapp in mappings:
                        if int(mapp['metric_id']) == int(met['id']):
                            path_url = f"/{petstore_yaml['servers'][0]['url'].split('/')[-1]}{path}$"
                            assert mapp['pattern'] == path_url
                            assert mapp['http_method'] == method.upper()
                if met['name'] == 'hits':
                    methods = met.methods.list()
                    # +1 is 'hits' metric
                    assert len(methods) + 1 == len(metrics)
                    for meth in methods:
                        if meth['friendly_name'] == name:
                            assert meth['description'] == pet['description']
    # +1 is 'hits' metric
    assert pet_number + 1 == len(metrics)


def test_activedocs(import_oas3, petstore_yaml, dest_client):
    """Checks imported activedocs"""
    service = import_oas3[3]
    acdoc = dest_client.active_docs.select_by(**{'service_id': service['id']})[0]
    assert acdoc['name'] == petstore_yaml['info']['title']
    assert acdoc['name'] == petstore_yaml['info']['title']
    assert acdoc['description'] == petstore_yaml['info']['description']
    assert acdoc['published']
    assert not acdoc['skip_swagger_validations']
    assert acdoc['body']


def test_anon_policy(import_oas3):
    """Checks imported ANON policy"""
    service = import_oas3[3]
    policies = service.proxy.list().policies.list()['policies_config']
    assert len(policies) == 2
    assert policies[0]['configuration']['auth_type'] == 'user_key'
    assert policies[0]['configuration']['user_key'] == USER_KEY
    assert policies[0]['enabled']
    assert policies[0]['name'] == 'default_credentials'
