"""Objects for managing ServiceMesh deployments"""
from contextlib import ExitStack
from typing import List

from openshift import Selector

from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.env import Environ


class ServiceMesh:
    """Class for working with Service mesh"""

    def __init__(self, openshift: OpenShiftClient, token: str, url: str, identifier: str) -> None:
        self.token = token
        self.url = url
        self.openshift = openshift
        self.identifier = identifier
        self._ingress_url = None
        self._destroy: List[Selector] = []

    def patch_credentials(self, credentials):
        """Patches credentials of currently tested 3scale into service mesh"""
        self.openshift.patch("handler",
                             credentials,
                             [
                                 {"op": "replace",
                                  "path": "/spec/params/access_token",
                                  "value": self.token
                                  },
                                 {"op": "replace",
                                  "path": "/spec/params/system_url",
                                  "value": self.url
                                  }
                             ], patch_type="json")

    def generate_credentials(self):
        """Genereate new set of credentials for 3scale adapter"""
        name = f"3scale-credentials-{self.identifier}"
        with ExitStack() as stack:
            self.openshift.prepare_context(stack)
            result = self.openshift\
                .select_resource("pod", {"app": "3scale-istio-adapter"})\
                .object()\
                .execute(["./3scale-config-gen",
                          f"--url={self.url}",
                          f"--name={name}",
                          f"--token={self.token}",
                          f"--namespace={self.openshift.project_name}"])

        resources = result.out().split("---\n")

        for resource in resources:
            if resource:
                selector = self.openshift.create(resource)
                self._destroy.append(selector)
        return name

    def destroy(self):
        """Destroy all resources creates by this instance"""
        for selector in self._destroy:
            selector.delete(ignore_not_found=True)

    @property
    def ingress_url(self):
        """Return URL of the ingress gateway"""
        if not self._ingress_url:
            route = self.openshift.routes["istio-ingressgateway"]
            if "tls" in route["spec"]:
                self._ingress_url = "https://" + route["spec"]["host"]

            self._ingress_url = "http://" + route["spec"]["host"]
        return self._ingress_url

    @property
    def environ(self) -> Environ:
        """Returns Environ object for manipulation of the adapter environment"""
        return self.openshift.deployment_environ("3scale-istio-adapter")


# pylint: disable=too-few-public-methods
class ServiceMeshFactory:
    """Factory for ServiceMesh instances"""
    def __init__(self, openshift: OpenShiftClient, token: str, url: str) -> None:
        self.openshift = openshift
        self.token = token
        self.url = url

    def create(self, identifier) -> ServiceMesh:
        """Returns new ServiceMesh instance"""
        return ServiceMesh(self.openshift, self.token, self.url, identifier)
