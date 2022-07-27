"""Test Toolbox command `3scale`"""

import re
import os

import pytest

from testsuite.toolbox import toolbox

pytestmark = pytest.mark.require_version("2.7")

# removed 'update' as unsupported command

TOOLBOX_COMMANDS = [
    'account', 'activedocs', 'application', 'application-plan', 'backend',
    'copy', 'help', 'import', 'method', 'metric', 'policies', 'policy-registry',
    'product', 'proxy', 'proxy-config', 'remote', 'service'
    ]

TOOLBOX_SUBCOMMANDS = {
    'account': ['find'],
    'activedocs': ['apply', 'create', 'delete', 'list'],
    'application': ['apply', 'create', 'delete', 'list', 'show'],
    'application-plan': ['apply', 'create', 'delete', 'export', 'import', 'list', 'show'],
    'backend': ['copy'],
    'copy': ['service'],
    'import': ['csv', 'openapi'],
    'method': ['apply', 'create', 'delete', 'list'],
    'metric': ['apply', 'create', 'delete', 'list'],
    'policies': ['export', 'import'],
    'policy-registry': ['copy'],
    'product': ['copy', 'export', 'import'],
    'proxy': ['deploy', 'show', 'update'],
    'proxy-config': ['deploy', 'export', 'list', 'promote', 'show'],
    'remote': ['add', 'list', 'remove', 'rename'],
    'service': ['apply', 'copy', 'create', 'delete', 'list', 'show'],
    }

RE_EXPR = re.compile(r'^\s+([^\s]+)\s+.*$')


def test_cli_cmd_list():
    """Check the list of commands"""
    out = toolbox.run_cmd('')
    assert not out['stderr']
    out = out['stdout']

    lines = out.split(os.linesep)
    begin = lines.index('COMMANDS')
    end = lines.index('OPTIONS')
    toolbox_cmds = sorted([RE_EXPR.findall(line)[0] for line in lines[(begin + 1):(end - 1)] if line])
    assert TOOLBOX_COMMANDS == toolbox_cmds


def test_cli_cmd_list_help():
    """Check the help page of commands"""
    batch_cmds = []
    for cmd in TOOLBOX_COMMANDS + ['']:
        batch_cmds += [' help ' + cmd, cmd + ' --help', cmd + ' -h']

    ret_val = toolbox.run_cmd(batch_cmds)
    for ret in ret_val:
        assert not ret['stderr']

    grouped_return_values = [ret_val[i*3:i*3+3] for i in range(int(len(ret_val)/3))]

    for cmd_set in grouped_return_values:
        assert cmd_set[0]['stdout'] == cmd_set[1]['stdout'] == cmd_set[2]['stdout']


def test_cli_subcmd_list():
    """Check list of subcommands of commands."""
    ret_val = toolbox.run_cmd(TOOLBOX_SUBCOMMANDS.keys())
    for ret in ret_val:
        assert not ret['stderr']
        out = ret['stdout']

        command = re.findall(r'^NAME\s*\n\s*([^\s]+) -.*', out, re.MULTILINE)
        lines = out.split(os.linesep)
        begin = lines.index('SUBCOMMANDS')
        end = lines.index('OPTIONS FOR 3SCALE')
        toolbox_cmds = sorted([RE_EXPR.findall(line)[0] for line in lines[(begin + 2):(end - 3)] if line])
        assert TOOLBOX_SUBCOMMANDS[command[0]] == toolbox_cmds


def test_cli_subcmd_list_help():
    """Check help page of subcommands"""
    batch_cmds = []
    for cmd, value in TOOLBOX_SUBCOMMANDS.items():
        for subcmd in value:
            batch_cmds.append(' '.join([' help', cmd, subcmd]))
            for help_cmd in [' --help', ' -h']:
                batch_cmds.append(' '.join([cmd, subcmd, help_cmd]))
    ret_val = toolbox.run_cmd(batch_cmds)
    for ret in ret_val:
        assert not ret['stderr']

    grouped_return_values = [ret_val[i*3:i*3+3] for i in range(int(len(ret_val)/3))]

    index = 0
    for cmd in TOOLBOX_SUBCOMMANDS.values():
        for _ in cmd:
            cmd_set = grouped_return_values[index]
            assert cmd_set[0]['stdout'] == cmd_set[1]['stdout'] == cmd_set[2]['stdout']
            index += 1


def test_cli():
    """Check 'version' parameter."""
    batch_cmds = ['-v', '--version']
    ret_val = toolbox.run_cmd(batch_cmds)

    for ret in ret_val:
        assert not ret['stderr']

    assert ret_val[0]['stdout'] == ret_val[1]['stdout']
