"""Provide a small client for interacting with Prometheus REST API."""
import time
from datetime import datetime
from typing import Optional, Callable

import backoff
import requests

# Prometheus has configured the scrape interval to 30s,
# the scrape interval for 3scale is configured in the
# 3scale-scrape-configs.yml file
PROMETHEUS_REFRESH = 31


# pylint: disable=too-few-public-methods
class PrometheusClient:
    """Prometheus REST API Client.

    Note: Contains only methods being used by actual tests.
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def get_metrics(self, target: str) -> set:
        """Get metrics for a specific target.

        Args:
            :param target: target.
        """
        params = {
            "match_target": "{container='%s'}" % target,
        }
        response = requests.get(f"{self.endpoint}/api/v1/targets/metadata", params=params)
        response.raise_for_status()
        metrics = response.json()
        return {m["metric"] for m in metrics["data"]}

    def get_metric(self, metric: str, timestamp: Optional[str] = None) -> dict:
        """Get a metric byt metric name.

        Args:
          :param metric: Metric name.
          :param timestamp: Evaluation timestamp in rfc3339 or unix_timestamp
        """
        params = {
            "query": metric,
        }
        if timestamp:
            params["time"] = timestamp

        response = requests.get(f"{self.endpoint}/api/v1/query", params=params)
        response.raise_for_status()
        return response.json()["data"]["result"]

    def get_targets(self) -> dict:
        """Get active targets information"""

        params = {
            "state": "active",
        }

        response = requests.get(f"{self.endpoint}/api/v1/targets", params=params)
        response.raise_for_status()
        return response.json()["data"]["activeTargets"]

    def has_metric(self, metric: str, trigger_request: Optional[Callable] = None) -> bool:
        """
        Returns true if the given metric is collected by the current settings
        of prometheus.
        Args:
            :param metric: the name of the metric to test
            :param trigger_request: a function triggering the metric,
            as it does not have to be always present in Prometheus.
            (e. g. fresh install)
            When empty, the trigger call is not invoked.
        """
        try:
            _has_metric = self.get_metric(metric) != []
            if not _has_metric and trigger_request is not None:
                # when testing on a new install, the metric does not have to be present
                trigger_request()
                # waits to refresh the prometheus metrics
                time.sleep(PROMETHEUS_REFRESH)
                _has_metric = self.get_metric(metric) != []

        except requests.exceptions.HTTPError:
            _has_metric = False

        return _has_metric

    def has_metrics(self, metric: str, target: str, trigger_request: Optional[Callable] = None) -> bool:
        """
        Returns true if the given metric is collected by the current settings
        of prometheus, with the selector 'container=$target'.
        Args:
            :param metric: the name of the metric to test
            :param target: the name of the container label
            :param trigger_request: a function triggering the metric,
            as it does not have to be always present in Prometheus.
            (e. g. fresh install)
            When empty, the trigger call is not invoked.
        """
        try:
            _has_metric = metric in self.get_metrics(target)
            if not _has_metric and trigger_request is not None:
                # when testing on a new install, the metric does not have to be present
                trigger_request()
                # waits to refresh the prometheus metrics
                self.wait_on_next_scrape(target)
                _has_metric = metric in self.get_metrics(target)

        except requests.exceptions.HTTPError:
            _has_metric = False

        return _has_metric

    def wait_on_next_scrape(self, target_container: str):
        """Block until next scrape for a container is finished"""
        after = datetime.utcnow()

        def _time_of_scrape(target_container: str):
            for target in self.get_targets():
                if "container" in target["labels"].keys() and target["labels"]["container"] == target_container:
                    return datetime.fromisoformat(target["lastScrape"][:19])
            return None

        @backoff.on_predicate(backoff.fibo, lambda x: not x, 8, jitter=None)
        def _wait_on_next_scrape():
            last_scrape = _time_of_scrape(target_container)
            if last_scrape is not None:
                return after < last_scrape
            return False

        last_scrape = _time_of_scrape(target_container)
        if after < last_scrape:
            return

        wait_time = PROMETHEUS_REFRESH - (after - last_scrape).seconds

        time.sleep(wait_time)
        _wait_on_next_scrape()
