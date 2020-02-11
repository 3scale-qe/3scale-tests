"""This module implements an openshift interface with openshift oc client wrapper."""

import enum
import math
from io import StringIO
from contextlib import ExitStack
from typing import List, Dict, Union

import yaml

import openshift as oc

from testsuite.openshift.env import Environ
from testsuite.openshift.objects import Secrets, ConfigMaps


class SecretKinds(enum.Enum):
    """Secret kinds enum."""

    TLS = "tls"
    GENERIC = "generic"
    DOCKER_REGISTRY = "docker-registry"


class SecretTypes(enum.Enum):
    """Secret types enum."""

    OPAQUE = "opaque"
    BASIC_AUTH = "kubernetes.io/basic-auth"
    TLS = "kubernetes.io/ssl"


class Routes:
    """Dict-like interface to OpenShift routes"""

    def __init__(self, client) -> None:
        self._client = client

    def __iter__(self):
        """Return iterator for OpenShift routes"""
        data = yaml.load(
            StringIO(self._client.do_action("get", ["route", "-o", "yaml"]).out()),
            Loader=yaml.FullLoader)
        return iter([data] if data["kind"] == "Route" else data["items"])

    def __getitem__(self, name):
        """Return requested route in yaml format"""
        return yaml.load(
            StringIO(self._client.do_action("get", ["route", name, "-o", "yaml"]).out()),
            Loader=yaml.FullLoader)

    def for_service(self, service) -> list:
        """
        Return routes for specific service
        It will sort results by 3scale.net/tenant_id label
        Usage: getting routes for admin portal, master portal...
        :param service: service name in OpenShift
        :return: list of routes
        """
        routes = [r for r in self if r["spec"]["to"]["name"] == service]
        routes = list(sorted(routes,
                             key=lambda x: float(x["metadata"]["labels"].get("3scale.net/tenant_id", math.inf))))
        return routes


class OpenShiftClient:
    """OpenShiftClient is an interface to the official OpenShift python
    client."""

    def __init__(self, project_name: str, server_url: str = None, token: str = None):
        self.project_name = project_name
        self.server_url = server_url
        self.token = token

    def prepare_context(self, stack):
        """Prepare context fo executing commands"""
        if self.server_url is not None:
            stack.enter_context(oc.api_server(self.server_url))
        if self.token is not None:
            stack.enter_context(oc.token(self.token))
        stack.enter_context(oc.project(self.project_name))

    def do_action(self, verb: str, cmd_args: List[Union[str, List[str]]] = None,
                  auto_raise: bool = True) -> "oc.Selector":
        """Run an oc command."""
        cmd_args = cmd_args or []
        with ExitStack() as stack:
            self.prepare_context(stack)
            return oc.invoke(verb, cmd_args, auto_raise=auto_raise)

    @property
    def secrets(self):
        """Dict-like access to secrets"""

        return Secrets(self)

    @property
    def routes(self):
        """Interface to access OpenShift routes"""

        return Routes(self)

    @property
    def config_maps(self):
        """Dict-like access to config maps"""

        return ConfigMaps(self)

    def environ(self, deployment_name: str):
        """Dict-like access to environment variables of a deployment config """

        return Environ(openshift=self, deployment=deployment_name)

    def scale(self, deployment_name: str, replicas: int):
        """
        Scale an existing version of Deployment.
        Args:
            :param deployment_name: DeploymentConfig name
            :param replicas: scale up/down to this number
        """
        self.do_action("scale", ["--replicas=" + str(replicas), "dc", deployment_name])
        if replicas > 0:
            self._wait_for_scale(deployment_name)

    # pylint: disable=no-self-use
    def get_replicas(self, deployment_name: str):
        """
        Return number of replicas of Deployment
        Args:
            :param deployment_name: DeploymentConfig name
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
            selector = oc.selector("dc/" + deployment_name)
            deployment = selector.objects()[0]
            return deployment.model.spec.replicas

    def rollout(self, deployment_name: str):
        """Rollout a new version of a Deployment.

        Args:
            :param deployment_name: DeploymentConfig name
        """
        self.do_action("rollout", ["latest", deployment_name])
        self._wait_for_deployment(deployment_name)

    # pylint: disable=too-many-arguments
    def create_secret(self, name: str, kind: "SecretKinds", secret_type: "SecretTypes" = None,
                      literals: Dict[str, str] = None, files: Dict[str, str] = None,
                      cert_path: str = None, cert_key_path: str = None):
        """Create a new secret.

        Args:
            :param name: Secret name
            :param kind: The kind of the secret, given by SecretKinds
            :param secret_type: The type of the secret, given by SecretTypes
            :param literals: Speficy a key and literal value to insert in secret
            :param files: Key files key be specified using their file path,  in which case a default
                          name will be given to them, or optionally with a name and file path,
                          in which case the given name will be used.  Specifying a directory will
                          iterate each named file in the directory that is a valid secret key.
            :param cert_path: The path to the certificate
            :param cert_key_path: The path to the certificate key
        """
        opt_args = []

        if secret_type:
            opt_args.extend(["--type", secret_type.value])

        if literals:
            opt_args.extend([f"--from-literal={n}={v}" for n, v in literals.items()])

        if files:
            opt_args.extend([f"--from-file={n}={v}" for n, v in files.items()])

        if kind == SecretKinds.TLS:
            if cert_path is None or cert_key_path is None:
                raise ValueError("cert_path and cert_key_path required.")
            opt_args.extend(["--cert", cert_path, "--key", cert_key_path])

        self.do_action("create", ["secret", f"{kind.value}", f"{name}", opt_args])

    def new_app(self, source: str, params: Dict[str, str] = None):
        """Create application based on source code.

        Args:
            :param source: The source of the image, template or code that has a public repository
            :param params: The parameters to be passed to the source when building it
        """
        opt_args = []
        if params:
            opt_args.extend([f"--param={n}={v}" for n, v in params.items()])

        self.do_action("new-app", ["-f", source, opt_args])
        deployments = oc.selector("dc").qnames()
        for deployment in deployments:
            deployment_name = deployment.split("/")[1]
            self._wait_for_deployment(deployment_name)

    def add_volume(self, deployment_name: str, volume_name: str, mount_path: str,
                   secret_name: str = None):
        """Add volume to a given deployment.

        Args:
            :param deployment_name: The deployment name
            :param volume_name: The volume name
            :param mount_path: The path to be mounted
            :param secret_name: The name of an existing secret
        """
        self._manage_volume("add", deployment_name, volume_name, mount_path, secret_name)

    def remove_volume(self, deployment_name: str, volume_name: str):
        """Remove volume from a given deployment.

        Args:
            :param deployment_name: The deployment name
            :param volume_name: The volume name
        """
        self._manage_volume("remove", deployment_name, volume_name)

    # pylint: disable=too-many-arguments
    def _manage_volume(self, action: str, deployment_name: str, volume_name: str,
                       mount_path: str = None, secret_name: str = None):
        """Manage volumes for a given deployment.

        You can add or remove a volume by passing `add` or `remove` to :param action.

        Args:
            :param action: Either "add" or "remove" option
            :param deployment_name: The deployment name
            :param volume_name: The volume name
            :param mount_path: The path to be mounted
            :param secret_name: The name of an existing secret
        """
        opt_args = ["--name", volume_name]
        if mount_path:
            opt_args.extend([f"--mount-path", mount_path])

        if secret_name:
            opt_args.extend([f"--secret-name", secret_name])

        self.do_action("set", ["volume", f"dc/{deployment_name}", f"--{action}", opt_args])
        self._wait_for_deployment(deployment_name)

    def _wait_for_deployment(self, deployment_name: str):
        """Wait for a given deployment to be running.

        Args:
            :param deployment_name: The deployment name
        """
        self.do_action("rollout", ["status", deployment_name])

    def _wait_for_scale(self, deployment_name: str):
        """
        Wait for a given deployment to be scaled.
        Args:
            :param deployment_name: The deployment name
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
            # pylint: disable=no-member
            # https://github.com/PyCQA/pylint/issues/3137
            stack.enter_context(oc.timeout(90))

            dc_data = oc.selector(f"dc/{deployment_name}").object()
            dc_version = dc_data.model.status.latestVersion
            oc.selector(
                "pods",
                labels={
                    "deployment": f"{deployment_name}-{dc_version}"
                }
            ).until_all(
                success_func=lambda pod: (
                    pod.model.status.phase == "Running" and pod.model.status.containerStatuses[0].ready
                )
            )
