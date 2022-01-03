"""
Test Prometheus metric when worker starts
https://issues.redhat.com/browse/THREESCALE-5965
"""

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9.1')"),
              pytest.mark.disruptive,
              ]


def test_metric_worker(prometheus, production_gateway):
    """
    Test if metric worker counter will be increased when apicast worker is killed
    """
    metrics = prometheus.get_metric("worker_process")

    count_before = [m for m in metrics if m['metric']['container'] == 'apicast-production'][0]['value'][1]

    # There is no ps/top/htop in container, we need to search all processes and find out nginx: worker and kill him
    kill_worker = ('for k in /proc/[0-9]*;'
                   'do grep -i "^nginx: worker process" $k/cmdline 2>&1 >/dev/null;'
                   'if [[ $? == 0 ]]; then echo ${k##*/}; fi;'
                   'done | xargs kill -9')
    ocp = production_gateway.openshift
    pod = ocp.get_pod(production_gateway.deployment)
    ocp.do_action("exec", ['-ti', pod.names()[0], "--", "/bin/sh", "-c", kill_worker])

    # prometheus is downloading metrics periodicity, we need to wait for next fetch
    prometheus.wait_on_next_scrape("apicast-production")

    metrics = prometheus.get_metric("worker_process")

    count_after = [m for m in metrics if m['metric']['container'] == 'apicast-production'][0]['value'][1]

    assert int(count_after) == int(count_before) + 1
