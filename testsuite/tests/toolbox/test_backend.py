"""Tests for remote Toolbox feature"""

import re
import random
import string

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite.config import settings
from testsuite.toolbox import toolbox
import testsuite.utils
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.7')")

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]
# 'TRACE', 'CONNECT' are not supported by 3scale


@pytest.fixture(scope="module")
def my_backend(custom_backend):
    """Backend fixture"""
    return custom_backend(name=testsuite.utils.randomize("toolbox"))


def random_string(length=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


@pytest.fixture(scope="module")
def my_backend_metrics(request, my_backend):
    """Fixture for metrics"""
    metrics = []
    for _ in range(5):
        name = testsuite.utils.blame(request, "metric_")
        params = {"friendly_name": name, "description": testsuite.utils.blame_desc(request), "unit": random_string()}
        metric = my_backend.metrics.create(params=params)
        metrics.append(metric)
    yield metrics
    if not settings["skip_cleanup"]:
        for met in metrics:
            met.delete()


@pytest.fixture(scope="module")
def my_backend_methods(request, my_backend):
    """Fixture for methods"""
    methods = []
    # it is possible to create methods only for metric 'Hits'
    metr = my_backend.metrics.read_by(**{"friendly_name": "Hits"})
    for _ in range(5):
        name = testsuite.utils.blame(request, "method_")
        params = {"friendly_name": name, "description": testsuite.utils.blame_desc(request), "unit": random_string()}
        method = metr.methods.create(params=params)
        methods.append(method)
    yield methods
    if not settings["skip_cleanup"]:
        for met in methods:
            met.delete()


@pytest.fixture(scope="module")
def my_backend_mappings(my_backend, my_backend_metrics):
    """Fixture for mappings"""
    mapping_rules = []
    for metr in my_backend_metrics:
        for _ in range(5):
            params = {
                "metric_id": metr["id"],
                "pattern": "/" + random_string(),
                "http_method": random.choice(HTTP_METHODS),
                "delta": random.randint(0, 10000),
            }
            mapp = my_backend.mapping_rules.create(params=params)
            mapping_rules.append(mapp)
    yield mapping_rules
    if not settings["skip_cleanup"]:
        for mapp in mapping_rules:
            mapp.delete()


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def toolbox_copy(
    threescale_src1, threescale_dst1, my_backend, my_backend_metrics, my_backend_methods, my_backend_mappings
):
    """Toolbox copies backend from one 3scale instance to another one"""
    # pylint: disable=unused-argument
    copy_cmd = f"backend copy -s {threescale_src1} -d {threescale_dst1} "
    copy_cmd += f"{my_backend['system_name']}"
    ret = toolbox.run_cmd(copy_cmd)
    return ret


def test_copy(toolbox_copy, my_backend, my_backend_metrics, my_backend_methods, my_backend_mappings, dest_client):
    """Test for checking copied backend"""
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    (stdout, stderr) = (toolbox_copy["stdout"], toolbox_copy["stderr"])

    assert not stderr
    (s_back_id, s_system_name) = re.findall(r"source backend ID: (\d+) system_name: (\w+)", stdout)[0]
    assert my_backend["id"] == int(s_back_id)
    assert my_backend["system_name"] == s_system_name

    (t_back_id, t_system_name) = re.findall(r"target backend ID: (\d+) system_name: (\w+)", stdout)[0]
    dst_backend = dest_client.backends[int(t_back_id)]
    assert dst_backend["system_name"] == t_system_name

    metrics_cnt = re.findall(r"created (\d+) missing metrics", stdout)[0]
    methods_cnt = re.findall(r"created (\d+) missing methods", stdout)[0]
    maps_cnt = re.findall(r"created (\d+) mapping rules", stdout)[0]

    assert int(metrics_cnt) == len(my_backend_metrics)
    assert int(methods_cnt) == len(my_backend_methods)
    assert int(maps_cnt) == len(my_backend_mappings)
    # add cmp of backends
    toolbox.cmp_backends(my_backend, dst_backend)
