"""Tests for working with metrics of Toolbox feature"""

import re
import pytest

from dynaconf import settings

import testsuite
from testsuite import rawobj
from testsuite.utils import blame
import testsuite.toolbox.constants as constants
from testsuite.toolbox import toolbox


@pytest.fixture(scope="module")
def metric_obj(request, service):
    """
    Fixture for service with metric used in this test.
    Only metrics related to Product is supported.
    """
    obj = service
    name = testsuite.utils.blame(request, 'metric_')
    params = {
        'friendly_name': name,
        'unit': 'Hit'}
    metric = obj.metrics.create(params=params)
    yield obj
    if not settings["skip_cleanup"]:
        metric.delete()


@pytest.fixture(scope="module")
def my_app_plan(request, service, custom_app_plan):
    """Fixture for application plan to be able to test disability of metric."""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "silver")), service)


def disabled_metric(app_plan, metric):
    """Is metric disabled?"""
    return any([limit['value'] == 0 for limit in app_plan.limits(metric).list()])


def create_cmd(metric_obj, cmd, args=None):
    """Creates command for metric."""
    args = args or ''
    return f"metric {cmd} {constants.THREESCALE_SRC1} {metric_obj['id']} {args}"


def parse_create_command_out(out):
    """Parse output of command 'metric create'"""
    return re.match(r'Created metric id: (\d+). Disabled: (\w+)', out).groups()


@pytest.fixture(scope="module")
def empty_list(metric_obj):
    """Fixture for empty list constant"""
    return toolbox.run_cmd(create_cmd(metric_obj, 'list'))['stdout']


# Global variable for metrics' values to check
out_variables = {}


@pytest.mark.toolbox
def test_list1(empty_list, metric_obj):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd(metric_obj, 'list'))
    assert not ret['stderr']
    assert ret['stdout'] == empty_list
    assert re.findall(r'ID\tFRIENDLY_NAME\tSYSTEM_NAME\tUNIT\tDESCRIPTION', ret['stdout'])
    assert re.findall(r'\d+\s+Hits\s+hits\s+hit\s+Number of API hits', ret['stdout'])
    assert re.findall(r'\d+\s+metric[^\s]*\s+metric[^\s]*\s+Hit\s+\(empty\)', ret['stdout'])


@pytest.mark.toolbox
def test_create_metric1(metric_obj, my_app_plan):
    """Create metric1"""
    ret = toolbox.run_cmd(create_cmd(metric_obj, 'create', 'metric1 --description="metric1 desc"'))
    assert not ret['stderr']
    m_id, disabled = parse_create_command_out(ret['stdout'])
    met = metric_obj.metrics[int(m_id)]
    out_variables['metric1'] = met.entity
    assert disabled.lower() == 'false'
    assert not disabled_metric(my_app_plan, met)


@pytest.mark.toolbox
def test_create_metric2(metric_obj, my_app_plan):
    """Create metric2"""
    cmd = 'metric2 --disabled --description="metric2 desc" '
    cmd += '--system-name="metric_system" --unit="apple"'
    ret = toolbox.run_cmd(create_cmd(metric_obj, 'create', cmd))
    assert not ret['stderr']
    m_id, disabled = parse_create_command_out(ret['stdout'])
    met = metric_obj.metrics[int(m_id)]
    out_variables['metric_system'] = met.entity
    met = metric_obj.metrics[int(m_id)]
    assert disabled.lower() == 'true'
    assert disabled_metric(my_app_plan, met)


@pytest.mark.toolbox
def test_list2(empty_list, metric_obj):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd(metric_obj, 'list'))
    assert not ret['stderr']
    assert empty_list in ret['stdout']
    assert re.findall(r'\d+\s+metric1\s+metric1\s+hit\s+metric1 desc', ret['stdout'])
    assert re.findall(r'\d+\s+metric2\s+metric_system\s+apple\s+metric2 desc', ret['stdout'])


@pytest.mark.toolbox
def test_update_metric2(metric_obj):
    """Update metric2"""
    cmd = 'metric_system --enabled --description="metric3 desc changed" '
    cmd += '--unit="hit" --name="metric3"'
    ret = toolbox.run_cmd(create_cmd(metric_obj, 'apply', cmd))
    assert not ret['stderr']
    out_variables['metric3'] = metric_obj.metrics[int(out_variables['metric_system']['id'])].entity

    m_id = re.match(r'Applied metric id: (\d+); Enabled', ret['stdout']).groups()[0]
    assert int(m_id) == int(out_variables['metric_system']['id'])


@pytest.mark.toolbox
def test_delete_metrics(metric_obj):
    """Delete metrics"""
    for met in ['metric1', 'metric_system']:
        ret = toolbox.run_cmd(create_cmd(metric_obj, 'delete', met))
        assert not ret['stderr']
        m_id = re.match(r'Metric id: (\d+) deleted', ret['stdout']).groups()[0]
        assert int(m_id) == int(out_variables[met]['id'])


@pytest.mark.toolbox
def test_list3(empty_list, metric_obj):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd(metric_obj, 'list'))
    assert not ret['stderr']
    assert ret['stdout'] == empty_list


@pytest.mark.toolbox
def check_metrics():
    """Check values of created and updated metrics."""
    attr_list = constants.METRIC_CMP_ATTRS - {'system_name'}
    toolbox.check_object(out_variables['metric1'], attr_list, [
        'metric1 desc', 'metric1', 'metric1', 'metric1', 'hit'])
    toolbox.check_object(out_variables['metric_system'], attr_list, [
        'metric2 desc', 'metric_system', 'metric_system', 'metric2', 'apple'])
    toolbox.check_object(out_variables['metric3'], attr_list, [
        'metric1 desc', 'metric_system', 'metric3', 'metric_system', 'hit'])
