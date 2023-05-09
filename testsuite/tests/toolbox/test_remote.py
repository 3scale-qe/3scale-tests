"""Tests for remote Toolbox feature"""

import re

import pytest

from testsuite.config import settings

from testsuite.toolbox import toolbox


EMPTY_LIST = "Empty remote list.\n"


@pytest.fixture(scope="module")
def src1_str(testconfig):
    """Expected source remote config"""
    return f"^source {testconfig['threescale']['admin']['url']} {testconfig['threescale']['admin']['token']}$"


@pytest.fixture(scope="module")
def regexp_src1(src1_str):
    """Compiled expected source remote config"""
    return re.compile(src1_str)


@pytest.fixture(scope="module")
def regexp_dst1(dest_client):
    """Compiled expected destination remote config"""
    dst1_str = f"^destination {dest_client.url} {dest_client.token}$"
    return re.compile(dst1_str)


def create_cmd(cmd):
    """Creates command for command 'remote'"""
    return f"-c {settings['toolbox']['podman_cert_dir']}/toolbox_config.yaml remote {cmd}"


def test_list1():
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    assert ret["stdout"] == EMPTY_LIST


def test_add_src(threescale_src1):
    """Run command 'add source'"""
    ret = toolbox.run_cmd(create_cmd(f"add source {threescale_src1}"))
    assert not ret["stderr"]
    assert not ret["stdout"]


def test_add_dst(threescale_dst1):
    """Run command 'add destination'"""
    ret = toolbox.run_cmd(create_cmd(f"add destination {threescale_dst1}"))
    assert not ret["stderr"]
    assert not ret["stdout"]


def test_list2(regexp_src1, regexp_dst1):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    lines = ret["stdout"].splitlines()
    assert regexp_src1.match(lines[0]) is not None
    assert regexp_dst1.match(lines[2]) is not None


def test_rename():
    """Run command 'rename'"""
    ret = toolbox.run_cmd(create_cmd("rename source source_renamed"))
    assert not ret["stderr"]
    assert not ret["stdout"]


def test_list3(src1_str, regexp_dst1):
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    lines = ret["stdout"].splitlines()
    assert re.compile(src1_str.replace("source", "source_renamed", 1)).match(lines[2]) is not None
    assert regexp_dst1.match(lines[0]) is not None


def test_remove1():
    """Run command 'remove'"""
    ret = toolbox.run_cmd(create_cmd("remove destination"))
    assert not ret["stderr"]
    assert not ret["stdout"]


def test_remove2():
    """Run command 'remove'"""
    ret = toolbox.run_cmd(create_cmd("remove source_renamed"))
    assert not ret["stderr"]
    assert not ret["stdout"]


def test_list4():
    """Run command 'list'"""
    ret = toolbox.run_cmd(create_cmd("list"))
    assert not ret["stderr"]
    assert ret["stdout"] == EMPTY_LIST


def teardown_module(module):
    """Teardown for module - remove all remotes"""
    # pylint: disable=unused-argument
    if not settings["skip_cleanup"]:
        ret = toolbox.run_cmd(create_cmd("list"))
        if ret["stdout"] != EMPTY_LIST:
            line_reg = re.compile("^([^ ]*)")
            for remote in ret["stdout"].splitlines():
                remote_name = line_reg.match(remote).groups()[0]
                toolbox.run_cmd(create_cmd(f"remove {remote_name}"))
