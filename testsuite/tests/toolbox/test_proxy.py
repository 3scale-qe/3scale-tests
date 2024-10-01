"""Tests for working with proxy proxy of Toolbox feature"""

import json
import pytest

from testsuite.toolbox import toolbox

pytestmark = [
    pytest.mark.xdist_group(name="toolbox"),
]


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """Returns function of proxycfg command creation"""

    def _create_cmd(service, cmd, args=None):
        args = args or ""
        if isinstance(args, list):
            args = " ".join(args)
        return f"proxy {cmd} {threescale_src1} {service['id']} {args}"

    return _create_cmd


@pytest.fixture(scope="module")
def empty_show(service, create_cmd):
    """Fixture for empty show command"""
    return toolbox.run_cmd(create_cmd(service, "show"))["stdout"]


def test_proxy_show(service, create_cmd, empty_show):
    """Run command 'show'"""
    ret = toolbox.run_cmd(create_cmd(service, "show"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_show
    out_variables = json.loads(ret["stdout"])
    assert out_variables["service_id"] == service["id"]


def test_proxy_update(service, create_cmd, empty_show):
    """Run command 'update'"""
    out_variables = json.loads(empty_show)
    args = [
        "--param",
        f'error_auth_missing="{out_variables["error_auth_missing"]}_updated"',
        "--param",
        "error_status_auth_missing=505",
    ]
    ret = toolbox.run_cmd(create_cmd(service, "update", args))
    assert not ret["stderr"]


def test_proxy_show2(service, create_cmd):
    """Run command 'show'"""
    ret = toolbox.run_cmd(create_cmd(service, "show"))
    assert not ret["stderr"]

    out = json.loads(ret["stdout"])

    toolbox.cmp_ents(out, service.proxy.list().entity, out.keys())
