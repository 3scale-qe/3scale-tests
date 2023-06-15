"""
A simple interface to get data from Jaeger using the rest http api
Note: jaeger http rest api is not officially supported and may be a subject of a change
"""
from string import Template
from urllib.parse import urlparse
import backoff
import requests
import importlib_resources as resources


class Jaeger:
    """Wrapper for the Jaeger Api"""

    def __init__(self, endpoint: str, custom_config, verify):
        self.endpoint = endpoint
        self.verify = verify
        self.custom_config = custom_config

    @backoff.on_predicate(backoff.constant, lambda x: x["data"] == [], max_tries=10)
    def traces(self, service: str, operation: str):
        """
        Gets traces for given service and operation
        Tries again if the response does not contain any data
        :param service that the traces are of
        :param operation - operation of the traces
        :return: list of the traces
        """
        params = {"service": service, "operation": operation}
        response = requests.get(f"{self.endpoint}/api/traces", params=params, verify=self.verify)
        response.raise_for_status()

        return response.json()

    def apicast_config_open_telemetry(self, configmap_name, service_name):
        """
        :param configmap_name name of the configmap
        :param service_name how apicast using this configmap will be named in jaeger
        """
        collector_url = urlparse(self.custom_config["reporter"]["localCollectorHostPort"])
        config_file = resources.files("testsuite.resources.opentelemetry").joinpath("opentelemetry_config.ini")
        config_value = Template(config_file.read_text()).safe_substitute(
            {
                "host": collector_url.hostname,
                "port": collector_url.port,
                "service_name": service_name,
            }
        )
        return {configmap_name: config_value}
