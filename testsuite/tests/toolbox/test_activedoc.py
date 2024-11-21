"""Tests for Activedocs Toolbox feature"""

import re

import pytest

from testsuite.toolbox import constants
from testsuite.toolbox import toolbox
from testsuite.utils import blame, blame_desc, randomize
from testsuite import rawobj

SWAGGER_LINK = (
    "https://raw.githubusercontent.com/OAI/learn.openapis.org/refs/heads/main/examples/v2.0/json/petstore.json"
)

pytestmark = [
    pytest.mark.xdist_group(name="toolbox"),
]


@pytest.fixture(scope="module")
def my_app_plan(request, custom_app_plan, service):
    """App. plans fixture"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "silver")), service)


@pytest.fixture(scope="module")
def my_activedoc(request, service, oas3_body, custom_active_doc):
    """This fixture creates active document for service."""
    rawad = rawobj.ActiveDoc(
        name=blame(request, "activedoc"), service=service, body=oas3_body, description=blame_desc(request)
    )
    return custom_active_doc(rawad)


@pytest.fixture(scope="module")
def empty_list(service, my_app_plan, my_activedoc, create_cmd):
    """Fixture for empty list constant"""
    # these fixtures should be created for being able to list empty list
    # pylint: disable=unused-argument
    return toolbox.run_cmd(create_cmd("list"))["stdout"]


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """Returns function of activedocs command creation"""

    def _create_cmd(cmd, args=None):
        args = args or ""
        return f"activedocs {cmd} {threescale_src1} {args}"

    return _create_cmd


def parse_create_command_out(output):
    """Returns id from 'create' command output."""
    return re.match(r"ActiveDocs '([^']+)' has been created with ID: (\d+)", output).groups()


# Global variable for metrics' values to check
out_variables = {}


def test_list1(empty_list, service, my_app_plan, my_activedoc, create_cmd):
    """Run command 'list'"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list
    to_cmp = r"ID\tNAME\tSYSTEM_NAME\tSERVICE_ID\tPUBLISHED\tSKIP_SWAGGER_VALIDATIONS\tCREATED_AT\tUPDATED_AT"
    assert re.findall(to_cmp, ret["stdout"])
    to_cmp = rf"{my_activedoc['id']}\t{my_activedoc['name']}\t{my_activedoc['system_name']}\t"
    to_cmp += rf"{service['id']}\t{str(my_activedoc['published']).lower()}\t"
    to_cmp += rf"{str(my_activedoc['skip_swagger_validations']).lower()}\t"
    assert re.findall(to_cmp, ret["stdout"])


def test_create1(threescale, create_cmd):
    """Run command 'create' to create first activedoc"""
    out_variables["ac1_name"] = randomize("activedoc1", 3)
    ret = toolbox.run_cmd(create_cmd("create", f"{out_variables['ac1_name']} {SWAGGER_LINK}"))
    assert not ret["stderr"]

    out_variables["ac1"] = parse_create_command_out(ret["stdout"])
    out_variables["ac1_entity"] = threescale.active_docs[int(out_variables["ac1"][1])].entity


def test_create2(service, threescale, create_cmd):
    """Run command 'create' to create second activedoc"""
    out_variables["ac2_name"] = randomize("activedoc2", 3)
    cmd = f"{out_variables['ac2_name']} {SWAGGER_LINK} --service-id {service['id']} "
    cmd += '--skip-swagger-validations=true --description="activedoc2 desc" --published '
    cmd += f"--system-name={randomize('activedoc_system', 3)}"
    ret = toolbox.run_cmd(create_cmd("create", cmd))
    assert not ret["stderr"]

    out_variables["ac2"] = parse_create_command_out(ret["stdout"])
    out_variables["ac2_entity"] = threescale.active_docs[int(out_variables["ac2"][1])].entity


def test_list2(empty_list, service, my_activedoc, threescale, create_cmd):
    """Run command 'list' active docs"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    for line in empty_list.splitlines():
        assert line in ret["stdout"]

    to_cmp = rf"{out_variables['ac1_entity']['id']}\t{out_variables['ac1_entity']['name']}\t"
    to_cmp += rf"{out_variables['ac1_entity']['system_name']}\t\(empty\)\tfalse\tfalse"
    assert re.findall(to_cmp, ret["stdout"])
    to_cmp = rf"{out_variables['ac2_entity']['id']}\t{out_variables['ac2_entity']['name']}\t"
    to_cmp += rf"{out_variables['ac2_entity']['system_name']}\t{service['id']}\ttrue\ttrue"
    assert re.findall(to_cmp, ret["stdout"])


def test_apply1(service, threescale, create_cmd):
    """Run command 'apply' to update first activedoc"""
    cmd = rf"{out_variables['ac1_entity']['system_name']} --description='updated' "
    cmd += rf"--publish --service-id={service['id']} --name={out_variables['ac1_entity']['name'] + '_updated'} "
    cmd += r"--skip-swagger-validations=true "
    ret = toolbox.run_cmd(create_cmd("apply", cmd))
    assert not ret["stderr"]
    assert re.findall(rf"Applied ActiveDocs id: {out_variables['ac1'][1]}", ret["stdout"])
    out_variables["ac3"] = re.match(r"Applied ActiveDocs id: (\d+)", ret["stdout"]).groups()[0]
    out_variables["ac3_entity"] = threescale.active_docs[int(out_variables["ac3"])].entity


def test_delete1(create_cmd):
    """Run command 'delete' to delete first active doc"""
    ret = toolbox.run_cmd(create_cmd("delete", f"{out_variables['ac1'][1]}"))
    assert not ret["stderr"]
    assert f"ActiveDocs with id: {out_variables['ac1'][1]} deleted" in ret["stdout"]


def test_delete2(create_cmd):
    """Run command 'delete' to delete second active doc"""
    ret = toolbox.run_cmd(create_cmd("delete", f"{out_variables['ac2'][1]}"))
    assert not ret["stderr"]
    assert f"ActiveDocs with id: {out_variables['ac2'][1]} deleted" in ret["stdout"]


def test_list3(empty_list, create_cmd):
    """Run command 'list' active doc"""
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    assert empty_list in ret["stdout"]


def test_check_active_docs_values():
    """Check values of created and updated active docs."""
    # This comment shows clearly what attributes are checked
    # 'name', 'published', 'skip_swagger_validations', 'system_name'

    attr_list = constants.ACTIVEDOCS_CMP_ATTRS
    attr_list.add("body")
    # remove description because of https://issues.redhat.com/browse/THREESCALE-5836
    attr_list.add("description")
    toolbox.check_object(
        out_variables["ac1_entity"],
        attr_list,
        [out_variables["ac1_name"], False, False, out_variables["ac1_entity"]["system_name"]],
    )
    toolbox.check_object(
        out_variables["ac2_entity"],
        attr_list,
        [out_variables["ac2_name"], True, True, out_variables["ac2_entity"]["system_name"]],
    )
    toolbox.check_object(
        out_variables["ac3_entity"],
        attr_list,
        [out_variables["ac1_name"] + "_updated", True, True, out_variables["ac1_entity"]["system_name"]],
    )
