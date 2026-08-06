"""Tests for importing service(not product) from CSV Toolbox feature"""

import json
import random
import string

import pytest

from testsuite.config import settings
from testsuite.toolbox import toolbox

pytestmark = [
    pytest.mark.xdist_group(name="toolbox"),
]


@pytest.fixture(scope="module")
def policy_file(policy_configs):
    """Create file with policies definition"""
    file_name = settings["toolbox"]["podman_cert_dir"] + "/"
    file_name += "".join(random.choice(string.ascii_letters) for _ in range(16))
    toolbox.copy_string_to_remote_file(json.dumps(policy_configs), file_name)

    return file_name


@pytest.fixture(scope="module")
def import_policies(threescale_src1, policy_file, service):
    """Import policies by Toolbox"""
    import_cmd = f"policies import {threescale_src1} {service['id']} -f "
    import_cmd += policy_file
    ret = toolbox.run_cmd(import_cmd)

    assert not ret["stderr"]

    yield ret["stdout"]
    if not settings["skip_cleanup"]:
        toolbox.run_cmd("rm -f " + policy_file, False)


@pytest.fixture(scope="module")
def export_policies(threescale_src1, service, import_policies):
    """Export policies by Toolbox"""
    # pylint: disable=unused-argument
    export_cmd = f"policies export {threescale_src1} {service['id']} -o json"
    ret = toolbox.run_cmd(export_cmd)

    assert not ret["stderr"]

    return ret["stdout"]


def test_import(import_policies, policy_configs, service):
    """Check imported policies."""
    assert len(import_policies) == 0
    cfgs = policy_configs.copy()
    cfgs.append({"name": "apicast", "version": "builtin", "configuration": {}, "enabled": True})
    assert cfgs == service.proxy.list().policies.list()["policies_config"]


def test_export(export_policies, policy_configs, service):
    """Check exported policies."""
    cfgs = policy_configs.copy()
    cfgs.append({"name": "apicast", "version": "builtin", "configuration": {}, "enabled": True})
    assert cfgs == service.proxy.list().policies.list()["policies_config"] == json.loads(export_policies)
