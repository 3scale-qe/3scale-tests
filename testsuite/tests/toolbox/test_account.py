"""Tests for Services Toolbox feature"""

import re

import pytest

from testsuite.toolbox import toolbox


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """ Returns function of account command creation """

    def _create_cmd(cmd, args=None):
        args = args or ''
        return f"account {cmd} {threescale_src1} {args}"

    return _create_cmd


def parse_find_command_out(output):
    """Returns data from 'find' command output."""
    return re.match(r"id => (\d+)\n\norg_name => ([^\n ]+)", output, re.MULTILINE).groups()


def test_find_account_by_name(account, create_cmd):
    """Run command 'account find'"""
    ret = toolbox.run_cmd(create_cmd('find', account['org_name']))
    assert not ret['stderr']
    (acc_id, org_name) = parse_find_command_out(ret['stdout'])
    assert int(acc_id) == account['id']
    assert org_name == account['org_name']


def test_find_account_by_user(account, user, create_cmd):
    """Run command 'account find'"""
    # pylint: disable=unused-argument
    for acc_user in account.users.list():
        for attr in ['email', 'username']:
            ret = toolbox.run_cmd(create_cmd('find', acc_user[attr]))
            assert not ret['stderr']
            (acc_id, org_name) = parse_find_command_out(ret['stdout'])
            assert int(acc_id) == account['id']
            assert org_name == account['org_name']
