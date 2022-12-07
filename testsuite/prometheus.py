"""Provide a small client for interacting with Prometheus REST API."""
import logging
import time
from datetime import datetime, timedelta
from math import ceil
from typing import Optional, Callable, Dict
from urllib.parse import urljoin

import backoff
import requests

from testsuite import settings

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Prometheus has configured the scrape interval to 30s,
# the scrape interval for 3scale is configured in the
# 3scale-scrape-configs.yml file
PROMETHEUS_REFRESH = 30


# pylint: disable=too-few-public-methods
def _params(key: str = "", labels: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Generate prometheus query parameter from key and labels.

    returns: Formatted query string for Prometheus.
    Args:
      :param key: Key name to be queried in prometheus
      :param labels: Labels to be put inside {} of prometheus query
    """

    if not labels:
        return {"query": key}
    return {"query": "%s{%s}" % (key, ",".join(f"{k}='{v}'" for k, v in labels.items()))}


def get_metrics_keys(metrics: list):
    """get list of names from list returned by get_metrics"""
    return {m["metric"]["__name__"] for m in metrics}


class PrometheusClient:
    """Prometheus REST API Client.

    Note: Contains only methods being used by actual tests.
    """

    def __init__(self, endpoint: str, operator_based: bool = None):
        """
        Args:
            :param endpoint: url where prometheus is deployed
            :param operator_based: if prometheus is expected to gather new info based on PodMonitor or other CRD
        """
        self.endpoint = endpoint
        self.operator_based = operator_based

    def _do_request(self, path: str, **kwargs):
        """Make a request to prometheus api.

        Args:
            :param path: api endpoint to send request
            :param **kwargs: arguments passed to be passed to requests (e.g. params)
        """
        url = urljoin(self.endpoint, path)
        ssl_verify = settings["ssl_verify"]

        return requests.get(url, verify=ssl_verify, **kwargs)

    def get_metrics(self, key: str = "", labels: Optional[Dict[str, str]] = None) -> list:
        """Get a metric by metric key or labels.

        Args:
          :param key: Key name to be queried in prometheus
          :param labels: Labels to be put inside {} of prometheus query
        """
        params = _params(key, labels)

        response = self._do_request("/api/v1/query", params=params)
        response.raise_for_status()
        return response.json()["data"]["result"]

    def get_targets(self) -> dict:
        """Get active targets information"""

        params = {"state": "active"}

        response = self._do_request("/api/v1/targets", params=params)
        response.raise_for_status()
        return response.json()["data"]["activeTargets"]

    def has_metric(self, metric: str, target: str = "", trigger_request: Optional[Callable] = None) -> bool:
        """
        Returns true if the given metric is collected by the current settings
        of prometheus.
        Args:
            :param metric: the name of the metric to test
            :param target: the name of the container label
            :param trigger_request: a function triggering the metric,
            as it does not have to be always present in Prometheus (e. g. fresh install).
            When empty, the trigger call is not invoked.
        """
        labels = None
        if target:
            labels = {"container": target}
        try:
            has_metric = len(self.get_metrics(key=metric, labels=labels)) > 0
            if not has_metric and trigger_request is not None:
                # when testing on a new install, the metric does not have to be present
                trigger_request()
                # waits to refresh the prometheus metrics
                if target:
                    self.wait_on_next_scrape(target)
                else:
                    time.sleep(PROMETHEUS_REFRESH + 2)
                has_metric = len(self.get_metrics(key=metric, labels=labels)) > 0

        except requests.exceptions.HTTPError:
            has_metric = False

        return has_metric

    def wait_on_next_scrape(self, target_container: str, after: Optional[datetime] = None):
        """Block until next scrape for a container is finished"""
        if after is None:
            after = datetime.utcnow()

        def _time_of_scrape():
            for target in self.get_targets():
                if "container" in target["labels"].keys() and target["labels"]["container"] == target_container:
                    return datetime.fromisoformat(target["lastScrape"][:19]), datetime.strptime(
                        target["discoveredLabels"]["__scrape_interval__"], "%Ss").second
            return None, PROMETHEUS_REFRESH

        last_scrape, scrape_interval = _time_of_scrape()

        till = after + timedelta(seconds=scrape_interval + 2)

        if last_scrape:
            if after < last_scrape:
                return
            num = ceil((after - last_scrape).total_seconds() / PROMETHEUS_REFRESH)

            till = last_scrape + timedelta(seconds=PROMETHEUS_REFRESH * num + 2)

        wait_time = (till - datetime.utcnow()).seconds
        log.info("Waiting %ss for prometheus scrape", wait_time)
        time.sleep(wait_time)

        @backoff.on_predicate(backoff.fibo, lambda x: not x, max_tries=10, jitter=None)
        def _wait_on_next_scrape():
            _last_scrape, _ = _time_of_scrape()
            if _last_scrape is not None:
                return after < _last_scrape
            return False

        _wait_on_next_scrape()
