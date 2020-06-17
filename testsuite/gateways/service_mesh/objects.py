"""Helper objects for Service mesh gateway"""
from testsuite.openshift.client import OpenShiftClient
from testsuite.openshift.env import Environ
from testsuite.requirements import ThreeScaleAuthDetails

# pylint: disable=too-few-public-methods
from testsuite.rhsso.rhsso import RHSSOServiceConfiguration


class Httpbin:
    """Class for manipulation Httpbin deployment in service mesh environment"""

    def __init__(self, openshift: OpenShiftClient, credentials, deployment, path) -> None:
        self.openshift = openshift
        self.credentials = credentials
        self.deployment = deployment
        self.path = path

    def patch_service(self, service_id):
        """Patches currently tested service into httpbin deployment"""
        self.openshift.patch("deployment",
                             self.deployment,
                             [
                                 {"op": "replace",
                                  "path": "/spec/template/metadata/labels/service-mesh.3scale.net~1service-id",
                                  "value": str(service_id)
                                  },
                                 {"op": "replace",
                                  "path": "/spec/template/metadata/labels/service-mesh.3scale.net~1credentials",
                                  "value": self.credentials
                                  },
                             ], patch_type="json")
        self.openshift.wait_for_ready(self.deployment)

    def create_policy(self, name: str, info: RHSSOServiceConfiguration):
        """Creates new Policy, used for OIDC authorization, for specific realm setup"""
        params = {
            "NAME": name,
            "TARGET": self.deployment,
            "ISSUER": info.issuer_url(),
            "JWKS": info.jwks_uri()
        }
        self.openshift.new_app("testsuite/resources/service_mesh/policy.yaml", params)

    def remove_policy(self, name: str):
        """Removes existing policy"""
        self.openshift.delete("Policy", name)


class ServiceMesh:
    """Class for working with Service mesh"""

    def __init__(self, openshift: OpenShiftClient, credentials, auth: ThreeScaleAuthDetails) -> None:
        self.auth = auth
        self.openshift = openshift
        self.credentials = credentials
        self._ingress_url = None

    def patch_credentials(self):
        """Patches credentials of currently tested 3scale into service mesh"""
        self.openshift.patch("handler",
                             self.credentials,
                             [
                                 {"op": "replace",
                                  "path": "/spec/params/access_token",
                                  "value": self.auth.token
                                  },
                                 {"op": "replace",
                                  "path": "/spec/params/system_url",
                                  "value": self.auth.url
                                  }
                             ], patch_type="json")

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
        """Returns Environ object for manipulation adapter environment"""
        return self.openshift.deployment_environ("3scale-istio-adapter")
