"""Tests for Services Toolbox feature"""

import re

import pytest

from testsuite.toolbox import constants
from testsuite.toolbox import toolbox
from testsuite.utils import randomize

pytestmark = [
    pytest.mark.xdist_group(name="toolbox"),
]


@pytest.fixture(scope="module")
def empty_list(service, create_cmd):
    """Fixture for empty list constant"""
    # pylint: disable=unused-argument
    return toolbox.run_cmd(create_cmd("list"))["stdout"]


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """Returns function of services command creation"""

    def _create_cmd(cmd, args=None):
        args = args or ""
        return f"service {cmd} {threescale_src1} {args}"

    return _create_cmd


def parse_create_command_out(output):
    """Returns id from 'create' command output."""
    return re.match(r"Service '([^']+)' has been created with ID: (\d+)", output).groups()


# Global variable for metrics' values to check
out_variables = {}


def test_list1(empty_list, service, create_cmd):
    """Run command 'list'"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list
    to_cmp = r"ID\tNAME\tSYSTEM_NAME"
    assert re.findall(to_cmp, ret["stdout"])
    to_cmp = rf"{service['id']}\t{service['name']}\t{service['system_name']}"
    assert re.findall(to_cmp, ret["stdout"])


def test_create1(threescale, create_cmd):
    """Run command 'create' to create first service"""
    out_variables["ser1_name"] = randomize("service1", 3)
    ret = toolbox.run_cmd(create_cmd("create", f"{out_variables['ser1_name']}"))
    assert not ret["stderr"]

    out_variables["ser1"] = parse_create_command_out(ret["stdout"])
    out_variables["ser1_entity"] = threescale.services[int(out_variables["ser1"][1])].entity


def test_create2(threescale, create_cmd):
    """Run command 'create' to create second service"""
    out_variables["ser2_name"] = randomize("service2", 3)
    cmd = f"{out_variables['ser2_name']} --authentication-mode=oidc "
    cmd += '--deployment-mode="hosted" --description="service2 desc" '
    ret = toolbox.run_cmd(create_cmd("create", cmd))
    assert not ret["stderr"]

    out_variables["ser2"] = parse_create_command_out(ret["stdout"])
    out_variables["ser2_entity"] = threescale.services[int(out_variables["ser2"][1])].entity


def test_list2(empty_list, service, threescale, create_cmd):
    """Run command 'list' services"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    for line in empty_list.splitlines():
        assert line in ret["stdout"]

    to_cmp = rf"{out_variables['ser1_entity']['id']}\t{out_variables['ser1_entity']['name']}\t"
    to_cmp += rf"{out_variables['ser1_entity']['system_name']}"
    assert re.findall(to_cmp, ret["stdout"])
    to_cmp = rf"{out_variables['ser2_entity']['id']}\t{out_variables['ser2_entity']['name']}\t"
    to_cmp += rf"{out_variables['ser2_entity']['system_name']}"
    assert re.findall(to_cmp, ret["stdout"])


def test_show2(threescale, create_cmd):
    """Run command 'show' second service"""
    # pylint: disable=unused-argument

    ret = toolbox.run_cmd(create_cmd("show", out_variables["ser2_entity"]["id"]))
    assert not ret["stderr"]

    to_cmp = "ID\tNAME\tSTATE\tSYSTEM_NAME\tBACKEND_VERSION\t"
    to_cmp += "DEPLOYMENT_OPTION\tSUPPORT_EMAIL\tDESCRIPTION\tCREATED_AT\tUPDATED_AT"
    assert re.findall(to_cmp, ret["stdout"])

    service2 = out_variables["ser2_entity"]
    to_cmp = rf"{service2['id']}\t{service2['name']}\t{service2['state']}\t{service2['system_name']}\t"
    to_cmp += rf"{service2['backend_version']}\t{service2['deployment_option']}\t"
    to_cmp += rf"{service2['support_email']}\t{service2['description']}\t"
    to_cmp += rf"{service2['created_at']}\t{service2['updated_at']}"
    assert re.findall(to_cmp, ret["stdout"])


def test_apply1(service, threescale, create_cmd):
    """Run command 'apply' to update first service"""
    # pylint: disable=unused-argument
    cmd = rf"{out_variables['ser1_entity']['system_name']} --description='updated' "
    cmd += rf"--name={out_variables['ser1_entity']['name'] + '_updated'} "
    cmd += r'--authentication-mode=oidc --deployment-mode="hosted"'
    ret = toolbox.run_cmd(create_cmd("apply", cmd))
    assert not ret["stderr"]
    assert re.findall(rf"Applied Service id: {out_variables['ser1'][1]}", ret["stdout"])
    out_variables["ser3"] = re.match(r"Applied Service id: (\d+)", ret["stdout"]).groups()[0]
    out_variables["ser3_entity"] = threescale.services[int(out_variables["ser3"])].entity


def test_delete1(create_cmd):
    """Run command 'delete' to delete first service"""
    ret = toolbox.run_cmd(create_cmd("delete", f"{out_variables['ser1'][1]}"))
    assert not ret["stderr"]
    assert f"Service with id: {out_variables['ser1'][1]} deleted" in ret["stdout"]


def test_delete2(create_cmd):
    """Run command 'delete' to delete second service"""
    ret = toolbox.run_cmd(create_cmd("delete", f"{out_variables['ser2'][1]}"))
    assert not ret["stderr"]
    assert f"Service with id: {out_variables['ser2'][1]} deleted" in ret["stdout"]


def test_list3(empty_list, create_cmd):
    """Run command 'list' service"""
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    assert empty_list in ret["stdout"]


def test_check_services_values():
    """Check values of created and updated services."""
    # This comment shows clearly what attributes are checked
    # 'backend_version', 'deployment_option', 'description', 'name', 'system_name'

    attr_list = constants.SERVICE_CMP_ATTRS
    attr_list = attr_list.union(["state", "end_user_registration_required", "buyer_can_select_plan"])
    attr_list = attr_list.union(["buyer_key_regenerate_enabled", "buyer_plan_change_permission"])
    attr_list = attr_list.union(["buyers_manage_apps", "buyers_manage_keys", "custom_keys_enabled"])
    attr_list = attr_list.union(["intentions_required", "mandatory_app_key", "referrer_filters_required"])
    attr_list.remove("system_name")
    toolbox.check_object(
        out_variables["ser1_entity"],
        attr_list,
        ["1", "hosted", out_variables["ser1_name"], out_variables["ser1_entity"]["system_name"]],
    )
    toolbox.check_object(
        out_variables["ser2_entity"],
        attr_list,
        ["oidc", "hosted", "service2 desc", out_variables["ser2_name"], out_variables["ser2_entity"]["system_name"]],
    )
    toolbox.check_object(
        out_variables["ser3_entity"],
        attr_list,
        [
            "oidc",
            "hosted",
            "updated",
            out_variables["ser1_name"] + "_updated",
            out_variables["ser1_entity"]["system_name"],
        ],
    )
