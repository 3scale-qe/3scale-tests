"""Provide a small client for interacting with Prometheus REST API."""
from typing import Optional

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

    def get_metrics(self, target: str) -> dict:
        """Get metrics for a specific target.

        Args:
            :param target: target.
        """
        params = {
            "match_target": "{job='%s'}" % target,
        }
        response = requests.get(f"{self.endpoint}/api/v1/targets/metadata", params=params)
        response.raise_for_status()
        return response.json()

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
