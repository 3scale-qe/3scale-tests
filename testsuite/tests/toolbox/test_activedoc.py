"""Tests for Activedocs Toolbox feature"""

import re

import pytest

import testsuite.toolbox.constants as constants
from testsuite.toolbox import toolbox
from testsuite.utils import blame, blame_desc
from testsuite import rawobj

SWAGGER_LINK='https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore.json'

@pytest.fixture(scope="module")
def service(request, custom_service):
    """Service fixture"""
    return custom_service({"name": blame(request, "svc")})


@pytest.fixture(scope="module")
def my_app_plan(request, custom_app_plan, service):
    """App. plans fixture"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "silver")), service)

@pytest.fixture(scope="module")
def my_activedoc(request, service, oas3_body, custom_active_doc):
    """This fixture creates active document for service."""
    rawad = rawobj.ActiveDoc(
                name=blame(request, 'activedoc'),
                service=service, body=oas3_body,
                description=blame_desc(request))
    return custom_active_doc(rawad)

@pytest.fixture(scope="module")
def empty_list(service, my_app_plan, my_activedoc):
    """Fixture for empty list constant"""
    # these fixtures should be created for being able to list empty list
    # pylint: disable=unused-argument
    return toolbox.run_cmd(create_cmd('list'))['stdout']


def create_cmd(cmd, args=None):
    """Creates command for activedocs"""
    args = args or ''
    return f"activedocs {cmd} {constants.THREESCALE_SRC1} {args}"


def parse_create_command_out(output):
    """Returns id from 'create' command output."""
    return re.match(r"ActiveDocs '(\w+)' has been created with ID: (\d+)", output).groups()


# Global variable for metrics' values to check
out_variables = {}


@pytest.mark.toolbox
def test_list1(empty_list, service, my_app_plan, my_activedoc):
    """Run command 'list'"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('list'))
    assert not ret['stderr']
    assert ret['stdout'] == empty_list
    to_cmp = r'ID\tNAME\tSYSTEM_NAME\tSERVICE_ID\tPUBLISHED\tSKIP_SWAGGER_VALIDATIONS\tCREATED_AT\tUPDATED_AT'
    assert re.findall(to_cmp, ret['stdout'])
    to_cmp = fr"{my_activedoc['id']}\t{my_activedoc['name']}\t{my_activedoc['system_name']}"
    to_cmp += fr"{service['id']}\t{str(my_activedoc['published']).lower()}\t"
    to_cmp += fr"{str(my_activedoc['skip_swagger_validations']).lower()}\t"
    assert re.findall(to_cmp, ret['stdout'])


    @vars[:doc1] = parse_create_command_out @stdout2
    @vars[:doc1_ent] = @tbapi.default_client.active_docs[@vars[:doc1][:id].to_i].entity

    # create command for creating new activedoc 2
    cmd = "activedocs create #{threescale_src1} activedoc2 #{SWAGGER_LINK} "
    cmd += "--service-id #{@tbapi[:id]} --skip-swagger-validations=true "
    cmd += '--description="activedoc2 desc" --published --system-name="activedoc_system"'
    stds = run_cmd(cmd)
    @stderr3 = stds[:stderr]
    @stdout3 = stds[:stdout]
    @vars[:doc2] = parse_create_command_out @stdout3
    @vars[:doc2_ent] = @tbapi.default_client.active_docs[@vars[:doc2][:id].to_i].entity


@pytest.mark.toolbox
def test_create1(service):
    """Run command 'create' to create first activedoc"""
    ret = toolbox.run_cmd(create_cmd('create', f"activedoc1 {SWAGGER_LINK}"))
    assert not ret['stderr']

    out_variables['ac1'] = parse_create_command_out(ret['stdout'])
    out_variables['ac1_entity'] = service.app_plans[int(out_variables['plan1'][0])].entity


@pytest.mark.toolbox
def test_create2(service):
    """Run command 'create' to create second activedoc"""
    cmd = f"activedoc2 {SWAGGER_LINK} --service-id {service['id']} "
    cmd += '--skip-swagger-validations=true --description="activedoc2 desc" --published '
    cmd += '--system-name="activedoc_system"'
    ret = toolbox.run_cmd(create_cmd('create', cmd))
    assert not ret['stderr']

    out_variables['ac2'] = parse_create_command_out(ret['stdout'])
    out_variables['ac2_entity'] = service.app_plans[int(out_variables['plan2'][0])].entity


#@pytest.mark.toolbox
#def test_list2(empty_list, service, my_app_plans):
#    """Run command 'list' application plans"""
#    ret = toolbox.run_cmd(create_cmd('list', f"{service['id']}"))
#    assert not ret['stderr']
#    assert empty_list in ret['stdout']
#
#    assert re.findall(
#        fr"{my_app_plans[0]['id']}\t{my_app_plans[0]['name']}\t{my_app_plans[0]['system_name']}",
#        ret['stdout'])
#    assert re.findall(
#        fr"{my_app_plans[1]['id']}\t{my_app_plans[1]['name']}\t{my_app_plans[1]['system_name']}",
#        ret['stdout'])
#
#
#@pytest.mark.toolbox
#def test_show1(service):
#    """Run command 'show' to show first application"""
#    # pylint: disable=unused-argument
#    ret = toolbox.run_cmd(create_cmd('show', f"{service['id']} plan1sysname"))
#    assert not ret['stderr']
#
#    to_cmp = r'ID\tNAME\tSYSTEM_NAME\tAPPROVAL_REQUIRED\tEND_USER_REQUIRED\t'
#    to_cmp += r'COST_PER_MONTH\tSETUP_FEE\tTRIAL_PERIOD_DAYS'
#    assert re.findall(to_cmp, ret['stdout'])
#
#    to_cmp = fr"{out_variables['plan1'][0]}\tplan1\tplan1sysname\ttrue\tfalse\t11.1\t22.2\t33"
#    assert re.findall(to_cmp, ret['stdout'])
#
#
#@pytest.mark.toolbox
#def test_update1(service):
#    """Run command 'update' to update first application plan"""
#    cmd = f"{service['id']} plan1sysname --approval-required=false --cost-per-month=44 "
#    cmd += r'--enabled --setup-fee=55 --trial-period-days=66 --hide'
#    ret = toolbox.run_cmd(create_cmd('apply', cmd))
#    assert not ret['stderr']
#    assert re.findall(
#        fr"Applied application plan id: {out_variables['plan1'][0]}; Default: false; Enabled",
#        ret['stdout'])
#    out_variables['plan3'] = re.match(
#        r'Applied application plan id: (\d+); Default: (\w+); (Enabled); (Hidden)',
#        ret['stdout']).groups()
#    out_variables['plan3_entity'] = service.app_plans[int(out_variables['plan3'][0])].entity
#
#
#@pytest.mark.toolbox
#def test_delete1(service):
#    """Run command 'delete' to delete first application plan"""
#    ret = toolbox.run_cmd(create_cmd('delete', f"{service['id']} {out_variables['plan1'][0]}"))
#    assert not ret['stderr']
#    assert f"Application plan id: {out_variables['plan1'][0]} deleted" in ret['stdout']
#
#
#@pytest.mark.toolbox
#def test_delete2(service):
#    """Run command 'delete' to delete second application plan"""
#    ret = toolbox.run_cmd(create_cmd('delete', f"{service['id']} {out_variables['plan2'][0]}"))
#    assert not ret['stderr']
#    assert f"Application plan id: {out_variables['plan2'][0]} deleted" in ret['stdout']
#
#
#@pytest.mark.toolbox
#def test_list3(empty_list, service):
#    """Run command 'list' application plans"""
#    ret = toolbox.run_cmd(create_cmd('list', f"{service['id']}"))
#    assert not ret['stderr']
#    assert empty_list in ret['stdout']
#
#
#@pytest.mark.toolbox
#def test_check_application_plans_values(service):
#    """Check values of created and updated application plans."""
#    # pylint: disable=unused-argument
#    # This comment shows clearly what attributes are checked
#    # 'approval_required', 'cancellation_period', 'cost_per_month', 'custom', 'default',
#    # 'end_user_required', 'name', 'setup_fee', 'state', 'system_name', 'trial_period_days'
#
#    attr_list = constants.APP_PLANS_CMP_ATTRS
#    toolbox.check_object(out_variables['plan1_entity'], attr_list, [
#        True, 0, 11.1, False, True, False, 'plan1', 22.2, 'published', 'plan1sysname', 33])
#    toolbox.check_object(out_variables['plan2_entity'], attr_list, [
#        False, 0, 0, False, False, False, 'plan2', 0, 'hidden', 'plan2sysname', 0])
#    toolbox.check_object(out_variables['plan3_entity'], attr_list, [
#        False, 0, 44, False, True, False, 'plan1', 55, 'hidden', 'plan1sysname', 66])
