"""Module containing WASMExtension"""

import importlib_resources as resources
from threescale_api.resources import Service

from testsuite.openshift.client import OpenShiftClient


# pylint: disable=too-many-instance-attributes
class WASMExtension:
    """Class representing once instance of WASMExtension, including deployed Httpbin as there is 1:1 mapping"""
    # pylint: disable=too-many-arguments
    def __init__(self, httpbin: OpenShiftClient, mesh: OpenShiftClient, portal_endpoint,
                 portal_token, backend_endpoint, image, parent_label, service: Service) -> None:
        self.httpbin = httpbin
        self.mesh = mesh
        self.portal_endpoint = portal_endpoint
        self.portal_token = portal_token
        self.backend_endpoint = backend_endpoint
        self.base_path = resources.files('testsuite.resources.service_mesh')
        self._ingress_url = None

        self.service = service
        self.label = f"{parent_label}-{self.service['id']}"
        self.httpbin_name = f"httpbin-{self.service['id']}"
        self.httpbin.new_app(self.base_path.joinpath('httpbin.yaml'), {
            "NAME": self.httpbin_name,
            "LABEL": self.label,
        })

        self.extension_name = f"threescale-extension-{self.service['id']}"
        configuration = service.proxy.list().configs.list(env="production")[0]
        token = configuration["proxy_config"]["content"]["backend_authentication_value"]
        self.httpbin.new_app(self.base_path.joinpath('extension.yaml'), {
            "NAME": self.extension_name,
            "LABEL": self.label,
            "BACKEND_HOST": self.backend_endpoint,
            "SYSTEM_HOST": self.portal_endpoint,
            "SYSTEM_TOKEN": self.portal_token,
            "SERVICE_ID": service["id"],
            "SERVICE_TOKEN": token,
            "IMAGE": image,
            "SELECTOR": self.label
        })

    @property
    def ingress_url(self):
        """Return URL of the ingress gateway"""
        if not self._ingress_url:
            route = self.mesh.routes["istio-ingressgateway"]
            if "tls" in route["spec"]:
                self._ingress_url = "https://" + route["spec"]["host"]

            self._ingress_url = "http://" + route["spec"]["host"]
        return self._ingress_url

    def add_mapping_rules(self, rules):
        """Adds mapping rule into the extension
            Rules should contain list of rules that have attributes:
            http_method, pattern, metric_system_name, delta, last
        """
        ops = []
        for rule in rules:
            ops.append(
                {
                    "op": "add",
                    "path": "/spec/config/services/0/mapping_rules/-",
                    "value": {
                        "method": rule["http_method"],
                        "pattern": rule["pattern"],
                        "usages": [
                            {
                                "name": rule["metric_system_name"],
                                "delta": rule["delta"]
                            }
                        ],
                        "last": rule["last"]
                    }
                }
            )
        self.httpbin.patch("sme", self.extension_name, ops, patch_type="json")

    def remove_all_mapping_rules(self):
        """Remove all mapping rules in extension"""
        ops = [
            {
                "op": "remove",
                "path": "/spec/config/services/0/mapping_rules"
            },
            {
                "op": "add",
                "path": "/spec/config/services/0/mapping_rules",
                "value": []
            }
        ]

        self.httpbin.patch("sme", self.extension_name, ops, patch_type="json")

    def synchronise_mapping_rules(self):
        """Take all mapping rules from current production config and deploy in extension"""
        self.remove_all_mapping_rules()
        # warning: not using backoff that was before used on below function
        config = self.service.proxy.list().configs.latest(env="production")
        map_rules = config["content"]["proxy"]["proxy_rules"]
        self.add_mapping_rules(map_rules)

    def delete(self):
        """Deletes extension and all that it created from openshift"""
        self.httpbin.delete_app(self.label, resources="all,sme,gateway,virtualservice")
