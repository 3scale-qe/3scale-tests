"""Tests for working with proxy configurations of Toolbox feature"""

import re
import json
import pytest

from testsuite import rawobj
from testsuite.toolbox import toolbox


@pytest.fixture(scope="module")
def create_cmd(threescale_src1):
    """Returns function of proxycfg command creation"""

    def _create_cmd(service, cmd, args=None):
        args = args or ""
        return f"proxy-config {cmd} {threescale_src1} {service['id']} {args}"

    return _create_cmd


@pytest.fixture(scope="module")
def empty_list_staging(service, create_cmd):
    """Fixture for empty list command for staging"""
    return toolbox.run_cmd(create_cmd(service, "list", "staging"))["stdout"]


@pytest.fixture(scope="module")
def empty_list_production(service, create_cmd):
    """Fixture for empty list command for production"""
    return toolbox.run_cmd(create_cmd(service, "list", "production"))["stdout"]


@pytest.fixture(scope="module")
def hits(service):
    """Returns metric 'Hits'."""
    return service.metrics.select_by(**{"system_name": "hits"})[0]


# Global variable for proxy configurations' values to check
out_variables = {}


def test_list_staging1(service, empty_list_staging, create_cmd):
    """Run command 'list' staging"""
    ret = toolbox.run_cmd(create_cmd(service, "list", "staging"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list_staging
    assert re.findall(r"ID\tVERSION\tENVIRONMENT", ret["stdout"])
    assert re.findall(r"\d+\t1\tsandbox", ret["stdout"])


def test_list_production1(service, empty_list_production, create_cmd):
    """Run command 'list' production"""
    ret = toolbox.run_cmd(create_cmd(service, "list", "production"))
    assert not ret["stderr"]
    assert ret["stdout"] == empty_list_production
    assert re.findall(r"ID\tVERSION\tENVIRONMENT", ret["stdout"])


def test_show_staging1(service, create_cmd):
    """Run command 'show' staging"""
    ret = toolbox.run_cmd(create_cmd(service, "show", "staging"))
    assert not ret["stderr"]
    out_variables["staging"] = json.loads(ret["stdout"])


def test_promote1(service, create_cmd):
    """Run command 'promote'"""
    ret = toolbox.run_cmd(create_cmd(service, "promote"))
    assert not ret["stderr"]
    # this is "version 2" because there is autopromotion in testsuite
    assert re.findall("Proxy Configuration version 2 promoted to 'production'", ret["stdout"])


def test_show_production1(service, create_cmd):
    """Run command 'show' production"""
    ret = toolbox.run_cmd(create_cmd(service, "show", "production"))
    assert not ret["stderr"]
    out_variables["production"] = json.loads(ret["stdout"])


def test_update_staging(service):
    """Update staging environment"""
    # update proxy
    params = {}

    for key in ["error_auth_failed", "error_auth_missing", "error_no_match", "error_limits_exceeded"]:
        params[key] = out_variables["staging"]["content"]["proxy"][key] + "_updated"

    params["api_backend"] = "https://httpbin.org:443"
    params["api_test_path"] = "/post"
    proxy = service.proxy.list()
    proxy.update(params)


def test_deploy(service, create_cmd):
    """Test 'deploy' command."""
    cmd = create_cmd(service, "deploy")
    ret = toolbox.run_cmd(cmd.replace("-config", ""))
    proxy = service.proxy.list()
    assert not ret["stderr"]
    assert proxy.entity == json.loads(ret["stdout"])


def test_list1(service, hits, empty_list_staging, create_cmd):
    """List staging"""
    # adding new policy increases cfg version
    new_policy = rawobj.PolicyConfig(
        "headers",
        {
            "response": [
                {
                    "op": "add",
                    "header": "X-RESPONSE-CUSTOM-ADD",
                    "value_type": "plain",
                    "value": "Additional response header",
                }
            ],
            "request": [
                {
                    "op": "add",
                    "header": "X-REQUEST-CUSTOM-ADD",
                    "value_type": "plain",
                    "value": "Additional request header",
                }
            ],
            "enable": True,
        },
    )

    proxy = service.proxy.list()
    proxy.policies.append(new_policy)

    mapping_rules = proxy.mapping_rules.list()
    for mapping_rule in mapping_rules:
        mapping_rule.delete()

    proxy.mapping_rules.create(rawobj.Mapping(hits, "/ip"))
    proxy.mapping_rules.create(rawobj.Mapping(hits, "/anything", "POST"))

    ret = toolbox.run_cmd(create_cmd(service, "list", "staging"))
    assert not ret["stderr"]
    for line in empty_list_staging.splitlines():
        assert line in ret["stdout"]
    assert re.findall(r"\d+\t2\tsandbox", ret["stdout"])


def test_show_staging2(service, create_cmd):
    """Run command 'show' staging"""
    ret = toolbox.run_cmd(create_cmd(service, "show", "staging"))
    assert not ret["stderr"]
    out_variables["staging_updated"] = json.loads(ret["stdout"])


def test_promote2(service, create_cmd):
    """Run command 'promote'"""
    ret = toolbox.run_cmd(create_cmd(service, "promote"))
    assert not ret["stderr"]
    assert re.findall("Proxy Configuration version 5 promoted to 'production'", ret["stdout"])


def test_list_production2(service, empty_list_production, create_cmd):
    """Run command 'list' production"""
    ret = toolbox.run_cmd(create_cmd(service, "list", "production"))
    assert not ret["stderr"]
    assert empty_list_production in ret["stdout"]
    assert re.findall(r"ID\tVERSION\tENVIRONMENT", ret["stdout"])
    assert re.findall(r"\d+\t2\tproduction", ret["stdout"])


def test_show_production2(service, create_cmd):
    """Run command 'show' production"""
    ret = toolbox.run_cmd(create_cmd(service, "show", "production"))
    assert not ret["stderr"]
    out_variables["production_updated"] = json.loads(ret["stdout"])


def test_check_proxy_configurations():
    """Check values of created and updated proxy configurations."""
    assert out_variables["staging"]["environment"] == "sandbox"
    assert out_variables["production"]["environment"] == "production"

    assert int(out_variables["staging"]["id"]) + 1 == int(out_variables["production"]["id"])
    assert out_variables["staging"]["content"]["proxy"]["id"] == out_variables["production"]["content"]["proxy"]["id"]

    assert out_variables["staging"]["content"] == out_variables["production"]["content"]

    assert out_variables["staging_updated"]["environment"] == "sandbox"
    assert out_variables["production_updated"]["environment"] == "production"

    assert int(out_variables["staging_updated"]["id"]) + 1 == int(out_variables["production_updated"]["id"])
    assert (
        out_variables["staging_updated"]["content"]["proxy"]["id"]
        == out_variables["production_updated"]["content"]["proxy"]["id"]
    )

    assert out_variables["staging_updated"]["content"] == out_variables["production_updated"]["content"]
