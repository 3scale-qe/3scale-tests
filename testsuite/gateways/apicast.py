"""Collection of gateways that are Apicast-based"""
from typing import Dict
from urllib.parse import urlparse

from threescale_api.resources import Service

from testsuite.gateways.gateways import AbstractApicast, Capability
from testsuite.openshift.client import OpenShiftClient


class SystemApicast(AbstractApicast):
    """Apicast that is deployed with 3scale"""

    CAPABILITIES = [Capability.SAME_CLUSTER,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.APICAST,
                    Capability.PRODUCTION_GATEWAY]

    def __init__(self, staging: bool, configuration, openshift):
        super().__init__(staging, configuration, openshift)
        if staging:
            self.deployment_name = configuration["staging_deployment"]
        else:
            self.deployment_name = configuration["production_deployment"]
        self.openshift: OpenShiftClient = openshift()

    def get_service_settings(self, service_settings: Dict) -> Dict:
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        return proxy_settings

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment_name)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment_name)[name]

    def reload(self):
        self.openshift.rollout(f"dc/{self.deployment_name}")


class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed Apicast without ability to edit it"""

    CAPABILITIES = [Capability.APICAST]

    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)
        self.staging_endpoint = configuration["sandbox_endpoint"]
        self.production_endpoint = configuration["production_endpoint"]

        deployments = configuration["deployments"]
        if staging:
            self.deployment = deployments["staging"]
        else:
            self.deployment = deployments["production"]

        # Load openshift configuration
        self.project = configuration.get("project", "threescale")
        self.server = configuration.get("server", "default")
        self.openshift = openshift(server_name=self.server, project_name=self.project)

    def get_service_settings(self, service_settings: Dict) -> Dict:
        service_settings.update({
            "deployment_option": "self_managed"
        })
        return service_settings

    def get_proxy_settings(self, service: Service, proxy_settings: Dict) -> Dict:
        entity_id = service.entity_id
        proxy_settings.update({
            "sandbox_endpoint": self.staging_endpoint % entity_id,
            "endpoint": self.production_endpoint % entity_id
        })
        return proxy_settings

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment)[name]

    def reload(self):
        self.openshift.rollout(self.deployment)


class OperatorApicast(SelfManagedApicast):
    """Gateway for use with Apicast deployed by operator"""
    def __init__(self, staging: bool, configuration, openshift) -> None:
        super().__init__(staging, configuration, openshift)
        services = configuration["services"]
        self.service_staging = services["staging"]
        self.service_production = services["production"]

    def register_service(self, service: Service):
        entity_id = service.entity_id
        staging_url = urlparse(self.staging_endpoint % entity_id)
        prod_url = urlparse(self.production_endpoint % entity_id)
        self.openshift.routes.create(name=f"{entity_id}-staging",
                                     service=self.service_staging, hostname=staging_url.hostname)
        self.openshift.routes.create(name=f"{entity_id}-production",
                                     service=self.service_production, hostname=prod_url.hostname)

    def unregister_service(self, service: Service):
        del self.openshift.routes[f"{service.entity_id}-staging"]
        del self.openshift.routes[f"{service.entity_id}-production"]

    def set_env(self, name: str, value):
        raise NotImplementedError()

    def get_env(self, name: str):
        raise NotImplementedError()

    def reload(self):
        self.openshift.do_action("delete", ["pod", "--force",
                                            "--grace-period=0", "-l", f"deployment={self.deployment}"])
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(f"deployment/{self.deployment}")
