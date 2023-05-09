"""
Test Prometheus metric when worker starts
https://issues.redhat.com/browse/THREESCALE-5965
"""

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9.1')"),
    pytest.mark.disruptive,
]


def test_metric_worker(prometheus, production_gateway):
    """
    Test if metric worker counter will be increased when apicast worker is killed
    """

    ocp = production_gateway.openshift
    pods = production_gateway.deployment.get_pods().objects()
    pod = [pod for pod in pods if pod.model.status.phase == "Running"][0]
    pod_name = pod.name()

    labels = {"container": "apicast-production"}
    #  pod label is only propagated in operator based prometheus, in template based querying only by container is fine
    if prometheus.operator_based:
        labels["pod"] = pod_name

    count_before = prometheus.get_metrics("worker_process", labels)[0]["value"][1]

    # There is no ps/top/htop in container, we need to search all processes and find out nginx: worker and kill him
    kill_worker = (
        "for k in /proc/[0-9]*;"
        'do grep -i "^nginx: worker process" $k/cmdline 2>&1 >/dev/null;'
        "if [[ $? == 0 ]]; then echo ${k##*/}; fi;"
        "done | xargs kill -9"
    )
    ocp.do_action("exec", ["-ti", pod_name, "--", "/bin/sh", "-c", kill_worker])

    # prometheus is downloading metrics periodicity, we need to wait for next fetch
    prometheus.wait_on_next_scrape("apicast-production")

    count_after = prometheus.get_metrics("worker_process", labels)[0]["value"][1]

    assert int(count_after) == int(count_before) + 1
