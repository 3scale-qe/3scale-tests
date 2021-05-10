"""SelfManaged Apicast"""
from abc import ABC, abstractmethod
from typing import Dict

from threescale_api.resources import Service

from testsuite.gateways.gateways import AbstractApicast, GatewayRequirements
from testsuite.capabilities import Capability
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.objects import Routes
from testsuite.openshift.env import Environ


class SelfManagedApicastRequirements(GatewayRequirements, ABC):
    """Requirements for SelfManagedApicast"""
    @property
    @abstractmethod
    def staging_endpoint(self) -> str:
        """Returns staging endpoint"""

    @property
    @abstractmethod
    def production_endpoint(self) -> str:
        """Returns production endpoint"""

    @property
    @abstractmethod
    def staging_deployment(self) -> str:
        """Returns staging deployment"""

    @property
    @abstractmethod
    def production_deployment(self) -> str:
        """Returns production deployment"""


class SelfManagedApicast2(AbstractApicast):
    """Gateway for use with already deployed self-managed Apicast in OpenShift"""

    CAPABILITIES = [Capability.APICAST,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER]

    def __init__(self, openshift, name):
        self.staging = True
        self.secure = True

        self._oc = openshift
        self._name = name

        self._routes = []

    @property
    def name(self):
        """Symbolic name of the apicast, besides other used as deployment name"""
        if self.staging:
            return f"{self._name}-stage"
        return self._name

    def _routename(self, service):
        """name of route for given service"""
        route = f"{service.entity_id}"
        if self.staging:
            route = f"{route}-stage"
        return route

    def before_service(self, service_params: Dict) -> Dict:
        service_params.update({"deployment_option": "self_managed"})
        return service_params

    def before_proxy(self, service: Service, proxy_params: Dict) -> Dict:
        route = self._routename(service)
        self.add_route(route)

        host = self._oc.do_action("get", ["route", route, "-o", "jsonpath={$..spec..host}"]).out().strip()

        key = "sandbox_endpoint" if self.staging else "endpoint"
        url = f"https://{host}" if self.secure else f"http://{host}"
        proxy_params.update({key: url})
        return proxy_params

    def on_service_delete(self, service: Service):
        super().on_service_delete(service)
        self.delete_route(self._routename(service))

    def add_route(self, name, kind=Routes.Types.EDGE):
        """Adds new route for this apicast"""
        self._oc.routes.create(name, kind, service=self.name, **{"insecure-policy": "Allow"})
        self._routes.append(name)

    def delete_route(self, name):
        """Delete route"""
        if name in self._routes and name in self._oc.routes:
            del self._oc.routes[name]
            self._routes.remove(name)

    @property
    def environ(self) -> Environ:
        return self._oc.environ(self.name)

    def reload(self):
        self._oc.rollout(f"dc/{self.name}")

    def get_logs(self, since_time=None):
        return self._oc.get_logs(self.name, since_time=since_time)

    def connect_jaeger(self, jaeger, jaeger_randomized_name):
        """
        Modifies the apicast to send information to jaeger.
        Creates configmap and a volume, mounts the configmap into the volume
        Updates the required env vars
        :param jaeger instance of the Jaeger class carrying the information about the apicast_configuration
        :param jaeger_randomized_name: randomized name used for the name of the configmap and for
               the identifying name of the service in jaeger
        """
        service_name = jaeger_randomized_name
        config_map_name = f"{jaeger_randomized_name}.json"
        self._oc.config_maps.add(config_map_name, jaeger.apicast_config(config_map_name, service_name))
        self._oc.add_volume(self.name, "jaeger-config-vol", "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTRACING_TRACER": "jaeger",
                               "OPENTRACING_CONFIG": f"/tmp/jaeger/{config_map_name}"})

    def update_image_stream(self, image_stream: str, amp_release: str = "latest"):
        """
        Updates the image stream the deployment is using
        :param image_stream: name of the image stream
        :param amp_release: tag of the image stream
        """
        self._oc.patch("dc", self.name, {"spec": {
            "triggers": [{
                "imageChangeParams": {
                    "automatic": True,
                    "containerNames": [
                        self.name],
                    "from":{
                        "name": f"{image_stream}:{amp_release}"}},
                    "type": "ImageChange"},
                {"type": "ConfigChange"}]}})
        # pylint: disable=protected-access
        self._oc._wait_for_deployment(self.name)


class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed Apicast in OpenShift"""

    CAPABILITIES = {Capability.APICAST,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}

    def __init__(self, requirements: SelfManagedApicastRequirements) -> None:
        self.staging = requirements.staging
        if self.staging:
            self.deployment = requirements.staging_deployment
            self.endpoint = requirements.staging_endpoint
        else:
            self.deployment = requirements.production_deployment
            self.endpoint = requirements.production_endpoint
        # Load openshift configuration
        self.openshift: OpenShiftClient = requirements.current_openshift
        self.options = requirements

    def before_service(self, service_params: Dict) -> Dict:
        service_params.update({
            "deployment_option": "self_managed"
        })
        return service_params

    def before_proxy(self, service: Service, proxy_params: Dict) -> Dict:
        entity_id = service.entity_id
        key = "sandbox_endpoint" if self.staging else "endpoint"
        proxy_params.update({
            key: self.endpoint % entity_id
        })
        return proxy_params

    @property
    def environ(self) -> Environ:
        return self.openshift.environ(self.deployment)

    def reload(self):
        self.openshift.rollout(f"dc/{self.deployment}")

    def get_logs(self, since_time=None):
        return self.openshift.get_logs(self.deployment, since_time=since_time)

    def connect_jaeger(self, jaeger, jaeger_randomized_name):
        """
        Modifies the apicast to send information to jaeger.
        Creates configmap and a volume, mounts the configmap into the volume
        Updates the required env vars
        :param jaeger instance of the Jaeger class carrying the information about the apicast_configuration
        :param jaeger_randomized_name: randomized name used for the name of the configmap and for
               the identifying name of the service in jaeger
        """
        service_name = jaeger_randomized_name
        config_map_name = f"{jaeger_randomized_name}.json"
        self.openshift.config_maps.add(config_map_name, jaeger.apicast_config(config_map_name, service_name))
        self.openshift.add_volume(self.deployment, "jaeger-config-vol",
                                  "/tmp/jaeger/", configmap_name=config_map_name)
        self.environ.set_many({"OPENTRACING_TRACER": "jaeger",
                               "OPENTRACING_CONFIG": f"/tmp/jaeger/{config_map_name}"})

    def update_image_stream(self, image_stream: str, amp_release: str = "latest"):
        """
        Updates the image stream the deployment is using
        :param image_stream: name of the image stream
        :param amp_release: tag of the image stream
        """
        self.openshift.patch("dc", self.deployment, {"spec": {
            "triggers": [{
                "imageChangeParams": {
                    "automatic": True,
                    "containerNames": [
                        self.deployment],
                    "from":{
                        "name": f"{image_stream}:{amp_release}"}},
                    "type": "ImageChange"},
                {"type": "ConfigChange"}]}})
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.deployment)
