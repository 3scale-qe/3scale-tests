"""Module for scaling deployments"""
import typing
from contextlib import contextmanager

from testsuite.openshift.deployments import DeploymentConfig

if typing.TYPE_CHECKING:
    from testsuite.openshift.client import OpenShiftClient
    from testsuite.openshift.crd.apimanager import APIManager


# pylint: disable=too-few-public-methods
class Scaler:
    """
    Simple layer on top of pure openshift scaling commands that either scale directly
    or through an operator, if possible
    """

    DEPLOYMENT_MAPPINGS = {"backend-listener": "scale_backend", "apicast-production": "scale_apicast_production"}

    def __init__(self, client: "OpenShiftClient"):
        self.client = client
        self.operator_deploy = client.is_operator_deployment
        if self.operator_deploy:
            # Fetch the APIManager instance only once
            self.apimanager: "APIManager" = client.api_manager

    def _scale_component(self, deployment_name, replicas, wait_for_replicas=None):
        """Scales one component"""
        if deployment_name not in self.DEPLOYMENT_MAPPINGS:
            raise ValueError(f"Scaler does not support scaling of {deployment_name}")

        if self.operator_deploy:
            apimanager_func = getattr(self.apimanager, self.DEPLOYMENT_MAPPINGS[deployment_name])
            return apimanager_func(replicas, wait_for_replicas=wait_for_replicas)
        deployment = DeploymentConfig(self.client, f"dc/{deployment_name}")
        previous_replicas = deployment.get_replicas()
        deployment.scale(replicas)
        return previous_replicas

    @contextmanager
    def scale(self, deployment_name, replicas):
        """Context manager for scaling components"""
        previous_replicas = self._scale_component(deployment_name, replicas)
        try:
            yield previous_replicas
        finally:
            self._scale_component(deployment_name, previous_replicas, wait_for_replicas=previous_replicas)
