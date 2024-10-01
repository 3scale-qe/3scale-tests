"""Tests for Application Plans Toolbox feature"""

import string
import random
import re
import logging
import yaml

import pytest

from testsuite.config import settings
from testsuite.toolbox import constants
from testsuite.toolbox import toolbox
from testsuite.utils import blame
from testsuite import rawobj

pytestmark = [
    pytest.mark.xdist_group(name="toolbox"),
]


@pytest.fixture(scope="module")
def service(request, custom_service):
    """Service fixture"""
    return custom_service({"name": blame(request, "svc")})


@pytest.fixture(scope="module")
def my_app_plans(request, custom_app_plan, service):
    """App. plans fixture"""
    return (
        custom_app_plan(rawobj.ApplicationPlan(blame(request, "silver")), service),
        custom_app_plan(rawobj.ApplicationPlan(blame(request, "gold")), service),
    )


@pytest.fixture(scope="module")
def empty_list(service, my_app_plans, create_cmd):
    """Fixture for empty list constant"""
    # these fixtures should be created for being able to list empty list
    # pylint: disable=unused-argument
    return toolbox.run_cmd(create_cmd("list", f"{service['id']}"))["stdout"]


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """Returns function of app. plans command creation"""

    def _create_cmd(cmd, args=None):
        """Creates command for app. plans."""
        args = args or ""
        return f"application-plan {cmd} {threescale_src1} {args}"

    return _create_cmd


def parse_create_command_out(output):
    """Returns id from 'create' command output."""
    return re.match(r"Created application plan id: (\d+). Default: (\w+); Disabled: (\w+)", output).groups()


# Global variable for metrics' values to check
out_variables = {}


def test_list1(empty_list, service, my_app_plans, create_cmd):
    """Run command 'list'"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd("list", f"{service['id']}"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list
    assert re.findall(r"ID\tNAME\tSYSTEM_NAME", ret["stdout"])
    assert re.findall(
        rf"{my_app_plans[0]['id']}\t{my_app_plans[0]['name']}\t{my_app_plans[0]['system_name']}", ret["stdout"]
    )
    assert re.findall(
        rf"{my_app_plans[1]['id']}\t{my_app_plans[1]['name']}\t{my_app_plans[1]['system_name']}", ret["stdout"]
    )


PLANS = {
    "plan1": {
        "name": "plan1",
        "state": "published",
        "setup_fee": "22.2",
        "cost_per_month": "11.1",
        "trial_period_days": "33",
        "cancellation_period": "0",
        "approval_required": "true",
        "system_name": "plan1sysname",
    },
    "plan2": {
        "name": "plan2",
        "state": "hidden",
        "setup_fee": "0.0",
        "cost_per_month": "0.0",
        "trial_period_days": "0",
        "cancellation_period": "0",
        "approval_required": "false",
        "system_name": "plan2sysname",
    },
}


def test_create1(service, create_cmd):
    """Run command 'create' to create first application plan"""
    plan = PLANS["plan1"]
    cmd = f"{service['id']} {plan['name']} --approval-required={plan['approval_required']} "
    cmd += f"--cost-per-month={plan['cost_per_month']} --default --disabled "
    if plan["state"] == "published":
        cmd += "--publish "
    cmd += f"--setup-fee={plan['setup_fee']} --system-name={plan['system_name']} "
    cmd += f"--trial-period-days={plan['trial_period_days']}"

    ret = toolbox.run_cmd(create_cmd("create", cmd))
    assert not ret["stderr"]

    out_variables["plan1"] = parse_create_command_out(ret["stdout"])
    out_variables["plan1_entity"] = service.app_plans[int(out_variables["plan1"][0])].entity


def test_create2(service, create_cmd):
    """Run command 'create' to create second application plan"""
    plan = PLANS["plan2"]
    cmd = f"{service['id']} {plan['name']} --approval-required={plan['approval_required']} "
    cmd += f"--cost-per-month={plan['cost_per_month']} --setup-fee={plan['setup_fee']} "
    cmd += f"--system-name={plan['system_name']} --trial-period-days={plan['trial_period_days']}"
    ret = toolbox.run_cmd(create_cmd("create", cmd))
    assert not ret["stderr"]

    out_variables["plan2"] = parse_create_command_out(ret["stdout"])
    out_variables["plan2_entity"] = service.app_plans[int(out_variables["plan2"][0])].entity


def test_export(service, create_cmd):
    """Run command 'export' for app. plans."""
    for plan_name in ["plan1", "plan2"]:
        cmd = f"{service['id']} {PLANS[plan_name]['system_name']}"
        ret = toolbox.run_cmd(create_cmd("export", cmd))
        assert not ret["stderr"]
        yaml_out = yaml.load(ret["stdout"], Loader=yaml.SafeLoader)
        for attr, value in PLANS[plan_name].items():
            assert str(yaml_out["plan"][attr]).casefold() == value
        assert len(yaml_out["limits"]) == 0 or yaml_out["limits"][0] == {
            "metric_system_name": "hits",
            "period": "eternity",
            "value": 0,
        }
        assert len(yaml_out["metrics"]) == 0 or yaml_out["metrics"][0] == {
            "name": "hits",
            "system_name": "hits",
            "friendly_name": "Hits",
            "description": "Number of API hits",
            "unit": "hit",
        }
        assert not yaml_out["pricingrules"]
        assert not yaml_out["plan_features"]
        assert not yaml_out["methods"]


# deprecated plan -> 'cancellation_period': '10',
# methods -> 'parent_id': 'pears', this is ignored
FOR_IMPORT = {
    "limits": [
        {
            "metric_system_name": "pears",
            "period": "eternity",
            "plan_id": "plantest",
            "value": 10,
        }
    ],
    "pricingrules": [
        {
            "cost_per_unit": 1.1,
            "min": 1,
            "max": 11,
            "metric_system_name": "pears_m",
        }
    ],
    "plan_features": [],
    "metrics": [
        {
            "name": "pears",
            "system_name": "pears",
            "friendly_name": "Pears",
            "description": "Number of API hits",
            "unit": "hit",
        }
    ],
    "methods": [
        {
            "name": "pears_m",
            "system_name": "pears_m",
            "friendly_name": "Pears_m",
            "description": "Number of API hits",
        }
    ],
    "plan": {
        "name": "plantest",
        "state": "published",
        "setup_fee": "1.1",
        "cost_per_month": "10.5",
        "trial_period_days": "400",
        "approval_required": "true",
        "system_name": "plantest",
    },
}


def test_import(service, create_cmd):
    """Run command 'import' for app. plans.
    This test just checks 'plan' attributes."""
    fil_name = settings["toolbox"]["podman_cert_dir"] + "/"
    fil_name += "".join(random.choice(string.ascii_letters) for _ in range(16))
    str_import = yaml.dump(FOR_IMPORT, Dumper=yaml.SafeDumper)
    toolbox.copy_string_to_remote_file(str_import, fil_name)
    ret = toolbox.run_cmd(create_cmd("import", rf"{service['id']} --file={fil_name}"))
    assert not ret["stderr"]
    plan_id = re.match(r"Application plan created: (\d+)", ret["stdout"]).groups()[0]
    new_plan = service.app_plans.read(int(plan_id))
    for attr, value in FOR_IMPORT["plan"].items():
        assert str(new_plan[attr]).casefold() == value

    out_variables["new_plan"] = new_plan


def test_imported(service):
    """Check objects imported by command 'import'."""
    # pylint: disable=too-many-branches
    new_plan = out_variables["new_plan"]
    for metric in service.metrics.list():
        if metric["system_name"] == FOR_IMPORT["metrics"][0]["system_name"]:
            for metric_attr, metric_val in FOR_IMPORT["metrics"][0].items():
                assert str(metric[metric_attr]) == metric_val
            limit = new_plan.limits(metric).list()[0]
            for limit_attr, limit_val in FOR_IMPORT["limits"][0].items():
                if limit_attr == "plan_id":
                    assert str(limit_val) == str(new_plan["system_name"])
                elif limit_attr == "metric_system_name":
                    assert str(limit_val) == str(metric["system_name"])
                else:
                    assert str(limit[limit_attr]) == str(limit_val)
        if metric["system_name"].startswith("hits"):
            method = metric.methods.list()[0]
            for method_attr, method_val in FOR_IMPORT["methods"][0].items():
                if method_attr == "parent_id":
                    assert str(metric["system_name"]) == str(method_val)
                else:
                    assert str(method[method_attr]) == method_val
            pricing = new_plan.pricing_rules(method).list()[0]
            for pricing_attr, pricing_val in FOR_IMPORT["pricingrules"][0].items():
                if pricing_attr == "metric_system_name":
                    assert str(method["system_name"]) == str(pricing_val)
                else:
                    assert str(pricing[pricing_attr]) == str(pricing_val)


def test_list2(empty_list, service, my_app_plans, create_cmd):
    """Run command 'list' application plans"""
    ret = toolbox.run_cmd(create_cmd("list", f"{service['id']}"))
    assert not ret["stderr"]
    assert empty_list in ret["stdout"]

    assert re.findall(
        rf"{my_app_plans[0]['id']}\t{my_app_plans[0]['name']}\t{my_app_plans[0]['system_name']}", ret["stdout"]
    )
    assert re.findall(
        rf"{my_app_plans[1]['id']}\t{my_app_plans[1]['name']}\t{my_app_plans[1]['system_name']}", ret["stdout"]
    )


def test_show1(service, create_cmd):
    """Run command 'show' to show first application"""
    # pylint: disable=unused-argument
    ret = toolbox.run_cmd(create_cmd("show", f"{service['id']} plan1sysname"))
    assert not ret["stderr"]

    to_cmp = r"ID\tNAME\tSYSTEM_NAME\tAPPROVAL_REQUIRED\t"
    to_cmp += r"COST_PER_MONTH\tSETUP_FEE\tTRIAL_PERIOD_DAYS"
    assert re.findall(to_cmp, ret["stdout"])
    plan = PLANS["plan1"]

    # https://issues.redhat.com/browse/THREESCALE-5542
    to_cmp = rf"{out_variables['plan1'][0]}\t{plan['name']}\t{plan['system_name']}\t"
    to_cmp += rf"{plan['approval_required']}\t{plan['cost_per_month']}\t{plan['setup_fee']}\t"
    to_cmp += rf"{plan['trial_period_days']}"
    logging.error(to_cmp)
    assert re.findall(to_cmp, ret["stdout"])


def test_update1(service, create_cmd):
    """Run command 'update' to update first application plan"""
    cmd = f"{service['id']} plan1sysname --approval-required=false --cost-per-month=44 "
    cmd += r"--enabled --setup-fee=55 --trial-period-days=66 --hide"
    ret = toolbox.run_cmd(create_cmd("apply", cmd))
    assert not ret["stderr"]
    assert re.findall(
        rf"Applied application plan id: {out_variables['plan1'][0]}; Default: false; Enabled", ret["stdout"]
    )
    out_variables["plan3"] = re.match(
        r"Applied application plan id: (\d+); Default: (\w+); (Enabled); (Hidden)", ret["stdout"]
    ).groups()
    out_variables["plan3_entity"] = service.app_plans[int(out_variables["plan3"][0])].entity


def test_delete1(service, create_cmd):
    """Run command 'delete' to delete first application plan"""
    ret = toolbox.run_cmd(create_cmd("delete", f"{service['id']} {out_variables['plan1'][0]}"))
    assert not ret["stderr"]
    assert f"Application plan id: {out_variables['plan1'][0]} deleted" in ret["stdout"]


def test_delete2(service, create_cmd):
    """Run command 'delete' to delete second application plan"""
    ret = toolbox.run_cmd(create_cmd("delete", f"{service['id']} {out_variables['plan2'][0]}"))
    assert not ret["stderr"]
    assert f"Application plan id: {out_variables['plan2'][0]} deleted" in ret["stdout"]


def test_list3(empty_list, service, create_cmd):
    """Run command 'list' application plans"""
    ret = toolbox.run_cmd(create_cmd("list", f"{service['id']}"))
    assert not ret["stderr"]
    assert empty_list in ret["stdout"]


def test_check_application_plans_values(service):
    """Check values of created and updated application plans."""
    # pylint: disable=unused-argument
    # This comment shows clearly what attributes are checked
    # 'approval_required', 'cancellation_period', 'cost_per_month', 'custom', 'default',
    # 'end_user_required', 'name', 'setup_fee', 'state', 'system_name', 'trial_period_days'

    attr_list = constants.APP_PLANS_CMP_ATTRS
    toolbox.check_object(
        out_variables["plan1_entity"],
        attr_list,
        [True, 0, 11.1, False, True, "plan1", 22.2, "published", "plan1sysname", 33],
    )
    toolbox.check_object(
        out_variables["plan2_entity"], attr_list, [False, 0, 0, False, False, "plan2", 0, "hidden", "plan2sysname", 0]
    )
    toolbox.check_object(
        out_variables["plan3_entity"], attr_list, [False, 0, 44, False, True, "plan1", 55, "hidden", "plan1sysname", 66]
    )
