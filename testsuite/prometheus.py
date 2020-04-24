"""Provide a small client for interacting with Prometheus REST API."""
import requests


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
