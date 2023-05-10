"""Module containing WASMExtension"""

import importlib_resources as resources
from threescale_api.resources import Service

from testsuite.openshift.client import OpenShiftClient


# pylint: disable=too-many-instance-attributes
class WASMExtension:
    """Class representing once instance of WASMExtension, including deployed Httpbin as there is 1:1 mapping"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        httpbin: OpenShiftClient,
        mesh: OpenShiftClient,
        portal_endpoint,
        portal_token,
        backend_endpoint,
        image,
        parent_label,
        service: Service,
        pull_secret,
    ) -> None:
        self.httpbin = httpbin
        self.mesh = mesh
        self.portal_endpoint = portal_endpoint
        self.portal_token = portal_token
        self.backend_endpoint = backend_endpoint
        self.base_path = resources.files("testsuite.resources.service_mesh")
        self._ingress_url = None
        self._ingress_alias_url = None

        self.service = service
        self.label = f"{parent_label}-{self.service['id']}"
        self.httpbin_name = f"httpbin-{self.service['id']}"
        self.httpbin.new_app(
            self.base_path.joinpath("httpbin.yaml"),
            {
                "NAME": self.httpbin_name,
                "LABEL": self.label,
            },
        )

        self.extension_name = f"threescale-extension-{self.service['id']}"
        self.httpbin.new_app(
            self.base_path.joinpath("plugin.yaml"),
            {
                "NAME": self.extension_name,
                "LABEL": self.label,
                "BACKEND_HOST": self.backend_endpoint,
                "SYSTEM_HOST": self.portal_endpoint,
                "SYSTEM_TOKEN": self.portal_token,
                "SERVICE_ID": service["id"],
                "IMAGE": image,
                "SELECTOR": self.label,
                "PULL_SECRET": pull_secret,
            },
        )
        self.credentials = None

        self.httpbin.deployment(f"dc/{self.httpbin_name}").wait_for()

    @property
    def ingress_url(self):
        """Return URL of the ingress gateway"""
        if not self._ingress_url:
            route = self.mesh.routes["istio-ingressgateway"]
            if "tls" in route["spec"]:
                self._ingress_url = "https://" + route["spec"]["host"]
            else:
                self._ingress_url = "http://" + route["spec"]["host"]
        return self._ingress_url

    @property
    def ingress_alias_url(self):
        """Returns alias url dynamically made by service mesh."""
        if not self._ingress_alias_url:
            for route in self.mesh.routes:
                if self.httpbin_name in route["spec"]["host"]:
                    alias_route = route
            if "tls" in alias_route["spec"]:
                self._ingress_alias_url = "https://" + alias_route["spec"]["host"]
            else:
                self._ingress_alias_url = "http://" + alias_route["spec"]["host"]
        return self._ingress_alias_url

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
                    "path": "/spec/pluginConfig/services/0/mapping_rules/-",
                    "value": {
                        "method": rule["http_method"],
                        "pattern": rule["pattern"],
                        "usages": [{"name": rule["metric_system_name"], "delta": rule["delta"]}],
                        "last": rule["last"],
                    },
                }
            )
        self.httpbin.patch("wasmplugin", self.extension_name, ops, patch_type="json")

    def remove_all_mapping_rules(self):
        """Remove all mapping rules in extension"""
        ops = [
            {"op": "remove", "path": "/spec/pluginConfig/services/0/mapping_rules"},
            {"op": "add", "path": "/spec/pluginConfig/services/0/mapping_rules", "value": []},
        ]

        self.httpbin.patch("wasmplugin", self.extension_name, ops, patch_type="json")

    def synchronise_mapping_rules(self):
        """Take all mapping rules from current production config and deploy in extension"""
        self.remove_all_mapping_rules()
        # warning: not using backoff that was before used on below function
        config = self.service.proxy.list().configs.latest(env="production")
        map_rules = config["content"]["proxy"]["proxy_rules"]
        self.add_mapping_rules(map_rules)

    def replace_credentials(self, credentials):
        """Replaces previous credentials and deploys new into the extension.
        `credentials` contains list of credentials with attributes:
        label: one of "user_key" or "app_id" or "app_key",
        credential_location: one of "query_string", "header", "authorization", or "oidc"
        key: search key
        """
        ops = []
        for label in ["user_key", "app_id", "app_key"]:
            ops.extend(
                [
                    {"op": "remove", "path": f"/spec/pluginConfig/services/0/credentials/{label}"},
                    {"op": "add", "path": f"/spec/pluginConfig/services/0/credentials/{label}", "value": []},
                ]
            )

        for cred in credentials:
            obj = None
            if cred["credential_location"] in {"query_string", "header"}:
                obj = {cred["credential_location"]: {"keys": [cred["key"]]}}
            elif cred["credential_location"] == "authorization":
                raise NotImplementedError
            elif cred["credential_location"] == "oidc":
                obj = {
                    "filter": {
                        "path": ["envoy.filters.http.jwt_authn", "0"],
                        "keys": ["azp", "aud"],
                        "ops": [{"take": {"head": 1}}],
                    }
                }

            ops.append(
                {"op": "add", "path": f"/spec/pluginConfig/services/0/credentials/{cred['label']}/-", "value": obj}
            )

        self.httpbin.patch("wasmplugin", self.extension_name, ops, patch_type="json")

    def remove_credentials(self, labels):
        """Remove credential with 'label' from extension"""
        ops = []
        for label in labels:
            ops.extend(
                [
                    {"op": "remove", "path": f"/spec/pluginConfig/services/0/credentials/{label}"},
                    {"op": "add", "path": f"/spec/pluginConfig/services/0/credentials/{label}", "value": []},
                ]
            )

        self.httpbin.patch("wasmplugin", self.extension_name, ops, patch_type="json")

    def remove_all_credentials(self):
        """Remove all credentials in extension"""
        labels = ["user_key", "app_id", "app_key"]
        self.remove_credentials(labels)

    def synchronise_credentials(self):
        """
        Take credentials from current production config and deploy in extension
        only if credentials changed.
        Returns True if credentials changed or were not synchronised before, otherwise false
        """
        # warning: not using backoff that was before used on below function
        config = self.service.proxy.list().configs.latest(env="production")

        auth_app_id = config["content"]["proxy"]["auth_app_id"]
        auth_app_key = config["content"]["proxy"]["auth_app_key"]
        auth_user_key = config["content"]["proxy"]["auth_user_key"]

        # translate 3scale location values to WASM location values
        credentials_location = config["content"]["proxy"]["credentials_location"]
        translate = {"query": "query_string", "headers": "header", "authorization": "authorization"}
        credentials_location = translate[credentials_location]

        auth_method = config["content"]["proxy"]["authentication_method"]
        credentials = []
        if auth_method == Service.AUTH_USER_KEY:
            credentials.append({"label": "user_key", "key": auth_user_key, "credential_location": credentials_location})
        elif auth_method == Service.AUTH_APP_ID_KEY:
            credentials.append({"label": "app_id", "key": auth_app_id, "credential_location": credentials_location})
            credentials.append({"label": "app_key", "key": auth_app_key, "credential_location": credentials_location})
        elif auth_method == Service.AUTH_OIDC:
            credentials.append({"label": "app_id", "credential_location": "oidc"})

        if not self.credentials or self.credentials != credentials:
            self.credentials = credentials
            self.replace_credentials(credentials)
            return True
        return False

    def replace_authorities(self, authorities, wait=True, overwrite=True):
        """Replaces previous authorities and deploys new into the extension.
        :param authorities: An array of strings, each one representing the Authority of a URL to match.
        These strings do accept glob patterns supporting the *, + and ? matchers.
        :param wait: Wait for wasm syncing
        :param overwrite: if False than keep current authorities and just add new ones
        """
        ops = []
        if overwrite:
            ops.extend(
                [
                    {"op": "remove", "path": "/spec/pluginConfig/services/0/authorities"},
                    {"op": "add", "path": "/spec/pluginConfig/services/0/authorities", "value": []},
                ]
            )

        for authority in authorities:
            ops.append({"op": "add", "path": "/spec/pluginConfig/services/0/authorities/-", "value": authority})

        self.httpbin.patch("wasmplugin", self.extension_name, ops, patch_type="json")
        if wait:
            self.httpbin.deployment(f"dc/{self.httpbin_name}").rollout()

    def delete(self):
        """Deletes extension and all that it created from openshift"""
        self.httpbin.delete_app(self.label, resources="all,wasmplugin,gateways.networking.istio.io,virtualservice")
