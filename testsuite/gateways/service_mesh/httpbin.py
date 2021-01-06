"""Objects for managing Httpbin deployments"""

from testsuite.openshift.client import OpenShiftClient
from testsuite.rhsso.rhsso import RHSSOServiceConfiguration


class Httpbin:
    """Class for manipulation Httpbin deployment in service mesh environment"""

    def __init__(self, openshift: OpenShiftClient, identifier, credentials) -> None:
        self.openshift = openshift
        self.credentials = credentials
        self.name = f"httpbin-{identifier}"

        self.openshift.new_app("testsuite/resources/service_mesh/httpbin.yaml", {"NAME": self.name})
        self.openshift._wait_for_deployment(self.name)

    def destroy(self):
        """Deletes all the resources created by this instance"""
        self.openshift.delete_app(self.name, "all,virtualservice,gateway")

    def patch_service(self, service_id):
        """Patches currently tested service into httpbin deployment"""
        self.openshift.patch("dc",
                             self.name,
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
        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.name)

    def create_policy(self, name: str, info: RHSSOServiceConfiguration):
        """Creates new Policy, used for OIDC authorization, for specific realm setup"""
        params = {
            "NAME": name,
            "TARGET": self.name,
            "ISSUER": info.issuer_url(),
            "JWKS": info.jwks_uri()
        }
        self.openshift.new_app("testsuite/resources/service_mesh/policy.yaml", params)

    def remove_policy(self, name: str):
        """Removes existing policy"""
        self.openshift.delete("Policy", name)


# pylint: disable=too-few-public-methods
class HttpbinFactory:
    """Factory for creating Httpbin instances"""
    def __init__(self, openshift) -> None:
        self.openshift = openshift

    def create(self, identifier, credentials) -> Httpbin:
        """Creates new Httpbin instance"""
        return Httpbin(self.openshift, identifier, credentials)
