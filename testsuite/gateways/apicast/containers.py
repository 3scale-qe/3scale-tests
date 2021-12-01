"""Collection of gateways that run in containerized environment"""
from typing import Dict

from threescale_api.resources import Service

from testsuite.capabilities import Capability
from testsuite.gateways.apicast import AbstractApicast
from testsuite.openshift.env import Properties


class ContainerizedApicast(AbstractApicast):
    """
    Gateway intended for use with RHEL based APIcast deployed in containerized environments
    """
    CAPABILITIES = {Capability.APICAST}
    HAS_PRODUCTION = False

    def __init__(self, endpoint: str, staging: bool) -> None:
        self.endpoint = endpoint
        self.staging = staging

    def before_service(self, service_params: Dict) -> Dict:
        service_params.update({
            "deployment_option": "self_managed"
        })
        return service_params

    def before_proxy(self, service: Service, proxy_params: Dict) -> Dict:
        name = service.entity_id
        if self.staging:
            name = f"stage-{name}"
        proxy_params.update({
            "sandbox_endpoint": self.endpoint % name,
        })
        return proxy_params

    def reload(self):
        raise NotImplementedError()

    def get_logs(self, since_time=None):
        raise NotImplementedError()

    @property
    def environ(self) -> Properties:
        raise NotImplementedError("ContainerizedAPIcast doesn't support environ yet")
