"""Tests for importing OAS by Toolbox"""

import json
import random
import re
import string
from urllib.parse import urlparse

import importlib_resources as resources
import pytest
import yaml
from testsuite.config import settings

import testsuite.toolbox.constants as constants
from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuth
from testsuite.toolbox import toolbox
from testsuite.utils import blame

# authentization in 3scale and mapping to OAS(http://spec.openapis.org/oas/v3.0.3#security-scheme-object):
#
# - 1 token -> see uber.json
#  "securityDefinitions": {
#    "apiKey": { "type": "apiKey", "in": "header", "name": "X-API-KEY"}
#  },
#  "security": { "apiKey": [ ] }
#
# - 2 tokens - not implemented yet https://issues.redhat.com/browse/THREESCALE-3279
#
# - RHSSO -> oauth2 -> see petstore-expanded.yaml which contains flow used in other OAuth2 tests
#
#   - tokenUrl and authorizationUrl are ignored, so it is not possible to do any api calls,
# see https://issues.redhat.com/browse/THREESCALE-5925
#
# - RHSSO -> openId
# https://issues.redhat.com/browse/THREESCALE-5919


OAS_FILES = {'oas2': ['testsuite.resources.oas2', 'uber.json'],
             'oas3': ['testsuite.resources.oas3', 'petstore-expanded.yaml']}
USER_KEY = '123456'

POLICIES = {'policies_config': [
               {'name': 'apicast', 'version': 'builtin', 'configuration': {}, 'enabled': True},
               {'name': 'keycloak_role_check', 'version': 'builtin', 'configuration': {
                   'type': 'blacklist', 'scopes': [
                        {'realm_roles': [], 'client_roles': [{'name': 'read'}, {'name': 'write'}]}]},
                   'enabled': True}]}


@pytest.fixture(scope="module", params=['oas2', 'oas3'])
def oas(request):
    """Loads oas file"""
    fil_oas = None
    fil_txt = None
    if request.param == 'oas2':
        src = resources.files(OAS_FILES[request.param][0]).joinpath(OAS_FILES[request.param][1])
        with src.open('r') as opened_file:
            fil_oas = json.load(opened_file)
            parsed_url = urlparse(settings['threescale']['service']['backends']['httpbin'])
            fil_oas['host'] = parsed_url.netloc
    else:
        src = resources.files(OAS_FILES[request.param][0]).joinpath(OAS_FILES[request.param][1])
        with src.open('r') as oas3_fil:
            fil_oas = yaml.load(oas3_fil, Loader=yaml.SafeLoader)
            fil_oas['servers'][0]['url'] = settings['threescale']['service']['backends']['httpbin'] + '/anything'
        with src.open('r') as oas3_fil:
            fil_txt = oas3_fil.read()
            new_url = settings['threescale']['service']['backends']['httpbin'] + '/anything'
            fil_txt = fil_txt.replace('http://petstore.swagger.io/api', new_url)

    fil_name = settings['toolbox']['podman_cert_dir'] + '/'
    fil_name += ''.join(random.choice(string.ascii_letters) for _ in range(16))
    if request.param == 'oas2':
        toolbox.copy_string_to_remote_file(json.dumps(fil_oas), fil_name)
    else:
        toolbox.copy_string_to_remote_file(fil_txt, fil_name)

    return {'type': request.param, 'file': fil_oas, 'file_name': fil_name}


@pytest.fixture(scope="module")
def import_oas(dest_client, request, oas):
    """Import OAS by Toolbox"""
    import_cmd = f"import openapi -d {constants.THREESCALE_DST1} "
    import_cmd += oas['file_name']
    import_cmd += f" --default-credentials-userkey={USER_KEY} "
    import_cmd += f"--target_system_name={blame(request, 'svc').translate(''.maketrans({'-':'_', '.':'_'}))}"
    ret = toolbox.run_cmd(import_cmd)
    (_, service_id, service_name) = re.findall(
        r'^(Created|Updated) service id: (\d+), name: (.+)$', ret['stdout'], re.MULTILINE)[0]
    service = dest_client.services[int(service_id)]
    yield (ret, service_id, service_name, service)
    if not settings["skip_cleanup"]:
        service.delete()
        toolbox.run_cmd('rm -f ' + oas['file_name'], False)


@pytest.fixture(scope="module")
def account(custom_account, request, testconfig, dest_client, import_oas):
    "Preconfigured account existing over whole testing session"
    # pylint: disable=unused-argument
    iname = blame(request, "id")
    account = rawobj.Account(org_name=iname, monthly_billing_enabled=None, monthly_charging_enabled=None)
    account.update(dict(name=iname, username=iname, email=f"{iname}@anything.invalid"))
    return custom_account(threescale_client=dest_client, params=account)


@pytest.fixture(scope="module")
def app_plan(import_oas, account, custom_app_plan, request, oas):
    "app plan bound to the service"
    # pylint: disable=unused-argument
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), import_oas[3])


@pytest.fixture(scope="module")
def application(import_oas, account, custom_app_plan, custom_application, request, oas, app_plan):
    "application bound to the account, app_plan and service"
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    return custom_application(rawobj.Application(blame(request, "app"), app_plan))


def test_import(import_oas, oas):
    """Checks import results"""
    (ret, service_id, service_name, service) = import_oas
    assert not ret['stderr']
    assert int(service_id) == int(service['id'])
    assert oas['file']['info']['title'] == service_name
    assert re.findall(r'^Service proxy updated$', ret['stdout'], re.MULTILINE)
    assert re.findall(r'^destroying all mapping rules$', ret['stdout'], re.MULTILINE)
    for path in oas['file']['paths'].keys():
        for method in oas['file']['paths'][path].keys():
            path_url = {'oas2': lambda: f"{oas['file']['basePath']}",
                        'oas3': lambda: f"{urlparse(oas['file']['servers'][0]['url']).path}"}[oas['type']]
            path_url = f"{path_url()}{path}"
            assert re.findall(
                rf"^Created {method.upper()} {path_url}\$ endpoint$",
                ret['stdout'],
                re.MULTILINE)
    if oas['type'] == 'oas3':
        assert re.findall(r'^Service policies updated$', ret['stdout'], re.MULTILINE)


def test_service(import_oas, oas):
    """Checks importes service"""
    service = import_oas[3]
    assert service['description'] == oas['file']['info']['description']
    assert service['name'] == oas['file']['info']['title']


def test_metrics_mappings_oas2(import_oas, oas):
    """Checks imported metrics - oas2"""
    if oas['type'] == 'oas3':
        pytest.skip("This testcase is oas2 only.")

    service = import_oas[3]
    metrics = service.metrics.list()
    mappings = service.proxy.list().mapping_rules.list()

    metr_number = 0
    for path in oas['file']['paths'].keys():
        metr_number += len(oas['file']['paths'][path].keys())
    # +1 is 'hits' metric
    assert metr_number + 1 == len(metrics)

    for mapp in mappings:
        path = mapp['pattern'].split(oas['file']['basePath'])[1].rstrip('$')
        method = mapp['http_method'].lower()
        assert oas['file']['paths'][path][method]

        met = service.metrics[int(mapp['metric_id'])]
        assert oas['file']['paths'][path][method]['description'] == met['description']


def test_metrics_mappings_oas3(import_oas, oas):
    """Checks imported metrics - oas3"""
    # pylint: disable=too-many-nested-blocks
    if oas['type'] == 'oas2':
        pytest.skip("This testcase is oas3 only.")

    service = import_oas[3]
    metrics = service.metrics.list()
    mappings = service.proxy.list().mapping_rules.list()

    pet_number = 0
    base_path = urlparse(oas['file']['servers'][0]['url']).path
    for path in oas['file']['paths'].keys():
        for method in oas['file']['paths'][path].keys():
            pet = oas['file']['paths'][path][method]
            name = pet['operationId']
            for met in metrics:
                if met['friendly_name'] == name:
                    pet_number += 1
                    assert pet['description'] == met['description']
                    for mapp in mappings:
                        if int(mapp['metric_id']) == int(met['id']):
                            assert mapp['pattern'] == f"{base_path}{path}$"
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


def test_activedocs(import_oas, oas, dest_client):
    """Checks imported activedocs"""
    service = import_oas[3]
    acdoc = dest_client.active_docs.select_by(**{'service_id': service['id']})[0]
    assert acdoc['name'] == oas['file']['info']['title']
    if oas['type'] == 'oas3':
        assert acdoc['name'] == oas['file']['info']['title']
    assert acdoc['description'] == oas['file']['info']['description']
    assert acdoc['published']
    assert not acdoc['skip_swagger_validations']
    assert acdoc['body']


def test_security(import_oas, oas):
    """Checks imported ANON policy"""
    service = import_oas[3]
    proxy = service.proxy.list()
    policies = proxy.policies.list()['policies_config']
    oidc = service.oidc().read()['oidc_configuration']

    # this is used only for oas without security and param --default-credentials-userkey
    #    assert policies[0]['configuration']['auth_type'] == 'user_key'
    #    assert policies[0]['configuration']['user_key'] == USER_KEY
    #    assert policies[0]['enabled']
    #    assert policies[0]['name'] == 'default_credentials'

    if oas['type'] == 'oas2':
        assert len(policies) == 1
        assert proxy['credentials_location'] == 'headers'
        assert proxy['auth_app_key'] == 'app_key'
        assert proxy['auth_app_id'] == 'app_id'
        assert proxy['auth_user_key'] == 'X-API-KEY'
        assert oidc['standard_flow_enabled']

    if oas['type'] == 'oas3':
        assert len(policies) == 2
        assert policies[1]['name'] == 'keycloak_role_check'
        assert policies[1]['configuration']['type'] == 'whitelist'
        assert policies[1]['configuration']['scopes'][0]['client_roles'] == [{'name': 'read'}, {'name': 'write'}]
        assert policies[1]['enabled']
        assert oidc['direct_access_grants_enabled']


def test_request(import_oas, oas, rhsso_service_info, application):
    "test request using one api endpoint, tune oidc setup for oas3"
    service = import_oas[3]
    path = '/anything/products'
    if oas['type'] == 'oas3':
        # this url should be updated because of https://issues.redhat.com/browse/THREESCALE-5925
        update_params = dict(credentials_location='authorization',
                             oidc_issuer_endpoint=rhsso_service_info.authorization_url())
        proxy = service.proxy.list()
        proxy.update(params=update_params)
        pol = proxy.policies.list()
        pol.update(POLICIES)
        application.register_auth(
            'oidc', OIDCClientAuth.partial(rhsso_service_info, location='authorization'))
        path = '/anything/pets'

    client = application.api_client()
    response = client.get(path)
    assert response.status_code == 200
