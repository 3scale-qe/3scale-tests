"""Tests for Application Toolbox feature"""

import re

import pytest

import testsuite.toolbox.constants as constants
from testsuite.toolbox import toolbox
from testsuite.utils import blame
from testsuite import rawobj


@pytest.fixture(scope="module")
def my_services(custom_service, service, request):
    """Services fixture"""
    return (service, custom_service({"name": blame(request, "svc")}))


@pytest.fixture(scope="module")
def my_accounts(custom_account, account, request):
    """Accounts fixture"""
    iname = blame(request, "id")
    return (account, custom_account(params=dict(name=iname, username=iname, org_name=iname)))


@pytest.fixture(scope="module")
def my_account_users(request, user, custom_user, my_accounts, configuration):
    """Account users fixture"""
    username = blame(request, 'user')
    domain = configuration.superdomain
    user2 = custom_user(my_accounts[1],
                        dict(username=username, email=f"{username}@{domain}",
                             password=blame(request, ''), account_id=my_accounts[1]['id']))
    return (user, user2)


@pytest.fixture(scope="module")
def my_app_plans(request, custom_app_plan, my_services):
    """App. plans fixture"""
    return (custom_app_plan(rawobj.ApplicationPlan(blame(request, "silver")), my_services[0]),
            custom_app_plan(rawobj.ApplicationPlan(blame(request, "gold")), my_services[1]))


@pytest.fixture(scope="module")
def my_applications(request, custom_application, my_app_plans):
    "application bound to the account and service existing over whole testing session"
    return custom_application(rawobj.Application(blame(request, "silver_app"), my_app_plans[0]))


@pytest.fixture(scope="module")
def promote(request, my_services, my_accounts, my_app_plans, my_applications):
    "application bound to the account and service existing over whole testing session"
    # pylint: disable=unused-argument
    my_services[0].proxy.list()[0].promote()


@pytest.fixture(scope="module")
def empty_list(my_services, my_applications):
    """Fixture for empty list constant"""
    # these fixtures should be created for being able to list empty list
    # pylint: disable=unused-argument
    return toolbox.run_cmd(create_cmd('list', f"--service={my_services[0]['id']}"))['stdout']


def create_cmd(cmd, args=None):
    """Creates command for metric."""
    args = args or ''
    return f"application {cmd} {constants.THREESCALE_SRC1} {args}"


def parse_create_command_out(output):
    """Returns id from 'create' command output."""
    return re.match(r'Created application id: (\d+)', output).groups()[0]


# Global variable for metrics' values to check
out_variables = {}


@pytest.mark.toolbox
def test_list1(empty_list, my_services, my_applications):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd('list', f"--service={my_services[0]['id']}"))
    assert not ret['stderr']
    assert ret['stdout'] == empty_list
    assert re.findall(r'ID\tNAME\tSTATE\tENABLED\tACCOUNT_ID\tSERVICE_ID\tPLAN_ID', ret['stdout'])
    to_cmp = f"{my_applications['id']}" + r'\t' + f"{my_applications['name']}"
    to_cmp += r'\t' + f"{my_applications['state']}" + r'\t'
    to_cmp += str(my_applications['enabled']).lower()
    to_cmp += r'\t' + f"{my_applications['account_id']}" + r'\t' + f"{my_applications['service_id']}"
    to_cmp += r'\t' + f"{my_applications['plan_id']}"
    assert re.findall(to_cmp, ret['stdout'])


@pytest.mark.toolbox
def test_create_app1(my_services, my_accounts, my_app_plans):
    """Run command 'create' to create first application"""
    cmd = f"{my_accounts[0]['id']} {my_services[0]['id']} {my_app_plans[0]['id']} app1 --user-key=\"123456\""
    ret = toolbox.run_cmd(create_cmd('create', cmd))
    assert not ret['stderr']

    out_variables['app1'] = my_accounts[0].applications[int(parse_create_command_out(ret['stdout']))].entity


@pytest.mark.toolbox
def test_create_app2(my_services, my_accounts, my_app_plans):
    # these fixtures should be created for creating
    # pylint: disable=unused-argument
    """Run command 'create' to create second application"""
    cmd = f"{my_accounts[1]['id']} {my_services[1]['id']} {my_app_plans[1]['id']} app2 "
    cmd += r'--description="app 2 description" --application-id="123456" '
    cmd += r'--application-key="123456"'
    ret = toolbox.run_cmd(create_cmd('create', cmd))
    assert not ret['stderr']

    out_variables['app2'] = my_accounts[1].applications[int(parse_create_command_out(ret['stdout']))].entity


@pytest.mark.toolbox
def test_list2(empty_list, my_services, my_applications):
    """Run command 'create' to create second application"""
    # these fixtures should be created for listing
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('list', f"--service={my_services[0]['id']}"))
    assert not ret['stderr']
    assert empty_list in ret['stdout']
    to_cmp = f"{out_variables['app1']['id']}" + r'\tapp1\tlive\ttrue\t'
    to_cmp += f"{out_variables['app1']['account_id']}" + r'\t'
    to_cmp += f"{out_variables['app1']['service_id']}" + r'\t'
    to_cmp += f"{out_variables['app1']['plan_id']}"
    assert re.findall(to_cmp, ret['stdout'])


@pytest.mark.toolbox
def test_show_app2(my_services, my_accounts, my_app_plans):
    """Run command 'show' to show second application"""
    # these fixtures should be created for showing
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('show', f"{out_variables['app2']['id']}"))
    assert not ret['stderr']
    to_cmp = r'ID\tNAME\tDESCRIPTION\tSTATE\tENABLED\tACCOUNT_ID\tSERVICE_ID\tPLAN_ID'
    to_cmp += r'\tUSER_KEY\tAPPLICATION_ID'
    assert re.findall(to_cmp, ret['stdout'])
    to_cmp = f"{out_variables['app2']['id']}" + r'\tapp2\tapp 2 description\t'
    to_cmp += r'live\ttrue\t' + f"{my_accounts[1]['id']}" + r'\t'
    to_cmp += f"{my_services[1]['id']}" + r'\t' + f"{my_app_plans[1]['id']}"
    to_cmp += r'\t[0-9a-z]+\t\(empty\)'
    assert re.findall(to_cmp, ret['stdout'])


@pytest.mark.toolbox
def test_update_app1_1(my_services, my_accounts, my_app_plans):
    """Run command 'update' to update first application"""
    # these fixtures should be created for updating
    # pylint: disable=unused-argument
    cmd = f"{out_variables['app1']['id']} "
    cmd += "--description='app1 description updated' "
    cmd += "--name='app1name' "
    cmd += '--suspend '
    ret = toolbox.run_cmd(create_cmd('apply', cmd))
    assert not ret['stderr']
    assert re.findall(f"Applied application id: {out_variables['app1']['id']}; Suspended", ret['stdout'])

    out_variables['app3'] = my_accounts[0].applications[int(out_variables['app1']['id'])].entity


@pytest.mark.toolbox
def test_update_app1_2(my_services, my_accounts):
    """Run command 'update' to update first application again"""
    # these fixtures should be created for update
    # pylint: disable=unused-argument
    cmd = f"{out_variables['app1']['id']} " + r'--resume --user-key=345678 '
    ret = toolbox.run_cmd(create_cmd('apply', cmd))
    assert not ret['stderr']
    assert re.findall(f"Applied application id: {out_variables['app1']['id']}; Resumed", ret['stdout'])

    out_variables['app4'] = my_accounts[0].applications[int(out_variables['app1']['id'])].entity


@pytest.mark.toolbox
def test_list3(empty_list, my_services, my_accounts, my_app_plans, my_applications):
    """Run command 'list' applications"""
    # these fixtures should be created for listing
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('list'))
    assert not ret['stderr']
    for line in empty_list.splitlines():
        assert line in ret['stdout']
    to_cmp = f"{out_variables['app1']['id']}" + r'\tapp1name\tlive\ttrue\t'
    to_cmp += f"{my_accounts[0]['id']}" + r'\t'
    to_cmp += f"{my_services[0]['id']}" + r'\t'
    to_cmp += f"{my_app_plans[0]['id']}"
    assert re.findall(to_cmp, ret['stdout'])
    to_cmp = f"{out_variables['app2']['id']}" + r'\tapp2\tlive\ttrue\t'
    to_cmp += f"{my_accounts[1]['id']}" + r'\t' + f"{my_services[1]['id']}"
    to_cmp += r'\t' + f"{my_app_plans[1]['id']}"
    assert re.findall(to_cmp, ret['stdout'])


@pytest.mark.toolbox
def test_show_app1(my_applications):
    """Run command 'show' to show first application"""
    # my_applications and all related fixtures should be created for showing
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('show', f"{out_variables['app1']['id']}"))
    assert not ret['stderr']
    to_find = r'ID\tNAME\tDESCRIPTION\tSTATE\tENABLED\tACCOUNT_ID\tSERVICE_ID\tPLAN_ID'
    to_find += r'\tUSER_KEY\tAPPLICATION_ID'
    assert re.findall(to_find, ret['stdout'])
    to_cmp = f"{out_variables['app1']['id']}"
    to_cmp += r'\tapp1name\tapp1 description updated\tlive\ttrue\t'
    to_cmp += f"{out_variables['app1']['account_id']}" + r'\t'
    to_cmp += f"{out_variables['app1']['service_id']}" + r'\t'
    to_cmp += f"{out_variables['app1']['plan_id']}" + r'\t345678\t\(empty\)'
    assert re.findall(to_cmp, ret['stdout'])


@pytest.mark.toolbox
def test_delete_app2(my_applications):
    """Run command 'delete' to delete second application"""
    # my_applications and all related fixtures should be created for deletion
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('delete', f"{out_variables['app2']['id']}"))
    assert not ret['stderr']
    assert f"Application id: {out_variables['app2']['id']} deleted" in ret['stdout']


@pytest.mark.toolbox
def test_delete_app1(my_applications):
    """Run command 'delete' to delete first application"""
    # my_applications and all related fixtures should be created for deletion
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd('delete', "'345678'"))
    assert not ret['stderr']
    assert f"Application id: {out_variables['app1']['id']} deleted" in ret['stdout']


@pytest.mark.toolbox
def test_list4(empty_list, my_services):
    """Run command 'list' applications"""
    ret = toolbox.run_cmd(create_cmd('list', f" --service={my_services[0]['id']}"))
    assert not ret['stderr']
    assert empty_list == ret['stdout']


@pytest.mark.toolbox
def test_check_applications_values(my_services, my_accounts, my_app_plans):
    """Check values of created and updated proxy applications."""
    # This comment shows clearly what attributes are checked
    # 'account_id', 'description', 'enabled', 'end_user_required', 'name', 'plan_id',
    # 'service_id', 'state', 'user_key'

    attr_list = constants.APPLICATION_CMP_ATTRS - {'account_id', 'plan_id', 'service_id'}
    toolbox.check_object(out_variables['app1'], attr_list, [
        my_accounts[0]['id'], 'app1', True, False, 'app1', my_app_plans[0]['id'],
        my_services[0]['id'], 'live', '123456'])

    toolbox.check_object(out_variables['app3'], attr_list, [
        my_accounts[0]['id'], 'app1 description updated', False, False, 'app1name',
        my_app_plans[0]['id'], my_services[0]['id'], 'suspended', '123456'])

    toolbox.check_object(out_variables['app4'], attr_list, [
        my_accounts[0]['id'], 'app1 description updated', True, False, 'app1name',
        my_app_plans[0]['id'], my_services[0]['id'], 'live'])

    attr_list = attr_list.union({'user_key'})
    toolbox.check_object(out_variables['app2'], attr_list, [
        my_accounts[1]['id'], 'app 2 description', True, False, 'app2', my_app_plans[1]['id'],
        my_services[1]['id'], 'live'])
