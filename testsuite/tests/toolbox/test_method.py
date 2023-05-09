"""Tests for working with methods of Toolbox feature"""

import re
import pytest

from testsuite.config import settings

import testsuite
from testsuite import rawobj
from testsuite.utils import blame
from testsuite.toolbox import constants
from testsuite.toolbox import toolbox


@pytest.fixture(scope="module")
def hits(request, service):
    """Returns metric 'Hits' which is parent of all methods created by Toolbox.
    Also creates methods to check the 'list' command."""
    hits = service.metrics.select_by(**{"system_name": "hits"})[0]
    name = testsuite.utils.blame(request, "method_")
    params = {"friendly_name": name, "unit": "Hit"}
    method = hits.methods.create(params=params)
    yield hits
    if not settings["skip_cleanup"]:
        method.delete()


@pytest.fixture(scope="module")
def my_app_plan(request, service, custom_app_plan):
    """Fixture for application plan to be able to test disability of method."""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "silver")), service)


def disabled_method(app_plan, method):
    """Is method disabled?"""
    return any(limit["value"] == 0 for limit in app_plan.limits(method).list())


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """Returns function of method command creation"""

    def _create_cmd(service, cmd, args=None):
        args = args or ""
        return f"method {cmd} {threescale_src1} {service['id']} {args}"

    return _create_cmd


def parse_create_command_out(out):
    """Parse output of command 'method create'"""
    return re.match(r"Created method id: (\d+). Disabled: (\w+)", out).groups()


@pytest.fixture(scope="module")
def empty_list(service, hits, create_cmd):
    # pylint: disable=unused-argument
    # hits should be created for this fixture
    """Fixture for empty list constant"""
    return toolbox.run_cmd(create_cmd(service, "list"))["stdout"]


# Global variable for methods' values to check
out_variables = {}


def test_list1(empty_list, service, create_cmd):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd(service, "list"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list
    assert re.findall(r"ID\tFRIENDLY_NAME\tSYSTEM_NAME\tDESCRIPTION", ret["stdout"])


def test_create_method1(service, my_app_plan, hits, create_cmd):
    """Create method1"""
    ret = toolbox.run_cmd(create_cmd(service, "create", 'method1 --description="method1 desc"'))
    assert not ret["stderr"]
    m_id, disabled = parse_create_command_out(ret["stdout"])
    met = hits.methods[int(m_id)]
    out_variables["method1"] = met.entity
    assert disabled.lower() == "false"
    assert not disabled_method(my_app_plan, met)


def test_create_method2(service, my_app_plan, hits, create_cmd):
    """Create method2"""
    cmd = 'method2 --disabled --description="method2 desc" '
    cmd += '--system-name="method_system"'
    ret = toolbox.run_cmd(create_cmd(service, "create", cmd))
    assert not ret["stderr"]
    m_id, disabled = parse_create_command_out(ret["stdout"])
    met = hits.methods[int(m_id)]
    out_variables["method_system"] = met.entity
    met = hits.methods[int(m_id)]
    assert disabled.lower() == "true"
    assert disabled_method(my_app_plan, met)


def test_list2(empty_list, service, create_cmd):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd(service, "list"))
    assert not ret["stderr"]
    assert empty_list in ret["stdout"]
    assert re.findall(r"\d+\s+method1\s+method1\s+method1 desc", ret["stdout"])
    assert re.findall(r"\d+\s+method2\s+method_system\s+method2 desc", ret["stdout"])


def test_update_method2(service, hits, create_cmd):
    """Update method2"""
    cmd = 'method_system --enabled --description="method3 desc changed" '
    cmd += '--name="method3"'
    ret = toolbox.run_cmd(create_cmd(service, "apply", cmd))
    assert not ret["stderr"]
    out_variables["method3"] = hits.methods[int(out_variables["method_system"]["id"])].entity

    m_id = re.match(r"Applied method id: (\d+); Enabled", ret["stdout"]).groups()[0]
    assert int(m_id) == int(out_variables["method_system"]["id"])


def test_delete_methods(service, create_cmd):
    """Delete method"""
    for met in ["method1", "method_system"]:
        ret = toolbox.run_cmd(create_cmd(service, "delete", met))
        assert not ret["stderr"]
        m_id = re.match(r"Method id: (\d+) deleted", ret["stdout"]).groups()[0]
        assert int(m_id) == int(out_variables[met]["id"])


def test_list3(empty_list, service, create_cmd):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd(service, "list"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list


def test_check_methods():
    """Check values of created and updated methods."""
    attr_list = constants.METRIC_METHOD_CMP_ATTRS - {"system_name"}
    toolbox.check_object(out_variables["method1"], attr_list, ["method1 desc", "method1", "method1", "method1"])
    toolbox.check_object(
        out_variables["method_system"], attr_list, ["method2 desc", "method2", "method_system", "method_system"]
    )
    toolbox.check_object(
        out_variables["method3"], attr_list, ["method3 desc changed", "method3", "method_system", "method_system"]
    )
