"""Objects for managing ServiceMesh deployments"""
from contextlib import ExitStack
from typing import List
from urllib.parse import urlparse, urlunparse

from openshift_client import Selector

from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.env import Properties


class ServiceMesh:
    """Class for working with Service mesh"""

    def __init__(self, openshift: OpenShiftClient, portal_endpoint, identifier: str) -> None:
        url = urlparse(portal_endpoint)
        self.token = url.username
        url = url._replace(netloc=url.hostname)
        self.url = urlunparse(url)

        self.openshift = openshift
        self.identifier = identifier
        self._ingress_url = None
        self._destroy: List[Selector] = []

    def patch_credentials(self, credentials):
        """Patches credentials of currently tested 3scale into service mesh"""
        self.openshift.patch(
            "handler",
            credentials,
            [
                {"op": "replace", "path": "/spec/params/access_token", "value": self.token},
                {"op": "replace", "path": "/spec/params/system_url", "value": self.url},
            ],
            patch_type="json",
        )

    def generate_credentials(self):
        """Genereate new set of credentials for 3scale adapter"""
        name = f"3scale-credentials-{self.identifier}"
        with ExitStack() as stack:
            self.openshift.prepare_context(stack)
            result = (
                self.openshift.select_resource("pod", {"app": "3scale-istio-adapter"})
                .object()
                .execute(
                    [
                        "./3scale-config-gen",
                        f"--url={self.url}",
                        f"--name={name}",
                        f"--token={self.token}",
                        f"--namespace={self.openshift.project_name}",
                    ]
                )
            )

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
    def environ(self) -> Properties:
        """Returns Environ object for manipulation of the adapter environment"""
        return self.openshift.environ("deployment/3scale-istio-adapter")
