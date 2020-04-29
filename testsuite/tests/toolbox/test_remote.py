"""Tests for remote Toolbox feature"""

import re
import pytest

from dynaconf import settings

import testsuite
import testsuite.toolbox.constants as constants
from testsuite.toolbox import toolbox


EMPTY_LIST = 'Empty remote list.\n'

SRC1_STR = f"^source {testsuite.CONFIGURATION.url} {testsuite.CONFIGURATION.token}$"
REGEXP_SRC1 = re.compile(SRC1_STR)
REGEXP_DST1 = re.compile(f"^destination {settings['toolbox']['destination_endpoint']} {settings['toolbox']['destination_provider_key']}$")  # noqa: E501 # pylint: disable=line-too-long


def create_cmd(cmd):
    """Creates command for command 'remote'"""
    return f"-c {settings['toolbox']['podman_cert_dir']}/toolbox_config.yaml remote {cmd}"


@pytest.mark.toolbox
def test_list1():
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd('list'))
    assert not ret['stderr']
    assert ret['stdout'] == EMPTY_LIST


@pytest.mark.toolbox
def test_add_src():
    """Run command 'add source'"""
    ret = toolbox.run_cmd(create_cmd(f"add source {constants.THREESCALE_SRC1}"))
    assert not ret['stderr']
    assert not ret['stdout']


@pytest.mark.toolbox
def test_add_dst():
    """Run command 'add destination'"""
    ret = toolbox.run_cmd(create_cmd(f"add destination {constants.THREESCALE_DST1}"))
    assert not ret['stderr']
    assert not ret['stdout']


@pytest.mark.toolbox
def test_list2():
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd('list'))
    assert not ret['stderr']
    lines = ret['stdout'].splitlines()
    assert REGEXP_SRC1.match(lines[0]) is not None
    assert REGEXP_DST1.match(lines[2]) is not None


@pytest.mark.toolbox
def test_rename():
    """Run command 'rename'"""
    ret = toolbox.run_cmd(create_cmd('rename source source_renamed'))
    assert not ret['stderr']
    assert not ret['stdout']


@pytest.mark.toolbox
def test_list3():
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd('list'))
    assert not ret['stderr']
    lines = ret['stdout'].splitlines()
    assert re.compile(SRC1_STR.replace('source', 'source_renamed')).match(lines[2]) is not None
    assert REGEXP_DST1.match(lines[0]) is not None


@pytest.mark.toolbox
def test_remove1():
    """Run command 'remove'"""
    ret = toolbox.run_cmd(create_cmd('remove destination'))
    assert not ret['stderr']
    assert not ret['stdout']


@pytest.mark.toolbox
def test_remove2():
    """Run command 'remove'"""
    ret = toolbox.run_cmd(create_cmd('remove source_renamed'))
    assert not ret['stderr']
    assert not ret['stdout']


@pytest.mark.toolbox
def test_list4():
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd('list'))
    assert not ret['stderr']
    assert ret['stdout'] == EMPTY_LIST


def teardown_module(module):
    """Teardown for module - remove all remotes"""
    # pylint: disable=unused-argument
    if not settings["skip_cleanup"]:
        ret = toolbox.run_cmd(create_cmd('list'))
        if ret['stdout'] != EMPTY_LIST:
            line_reg = re.compile('^([^ ]*)')
            for remote in ret['stdout'].splitlines():
                remote_name = line_reg.match(remote).groups()[0]
                toolbox.run_cmd(create_cmd(f"remove {remote_name}"))
