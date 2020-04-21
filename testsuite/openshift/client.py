"""This module implements an openshift interface with openshift oc client wrapper."""

import enum
import json
from contextlib import ExitStack
import os
from typing import List, Dict, Union, Any

import openshift as oc

from testsuite.openshift.env import Environ
from testsuite.openshift.objects import Secrets, ConfigMaps, Routes


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

    def patch(self, resource_type: str, resource_name: str, patch: Dict[str, Any], patch_type: str = None):
        """Patch the specified resource
        Args:
            :param resource_type: The resource type to be deleted. Ex.: service, route, deploymentconfig
            :param resource_name: The resource name to be patched
            :param patch: The patch to be applied to the resource
            :param patch_type: Optional. The type of patch being provided; one of [json merge strategic]
        """
        cmd_args = []
        if patch_type:
            cmd_args.extend(["--type", patch_type])

        patch_serialized = json.dumps(patch)
        self.do_action("patch", [resource_type, resource_name, cmd_args, "-p", patch_serialized])

    def apply(self, resource: Dict[str, Any]):
        """Apply the specified resource to the server.
        Args:
            :param resource: A dict containing the configuration to be applied
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
            oc.apply(resource)

    def delete(self, resource_type: str, name: str, force: bool = False):
        """Delete a resource.
        Args:
            :param resource_type: The resource type to be deleted. Ex.: service, route, deploymentconfig
            :param name: The resource name
            :param force: Pass --force to oc delete
        """
        args = []
        if force:
            args.append("-f")
        self.do_action("delete", [resource_type, name, args])

    def scale(self, deployment_name: str, replicas: int):
        """
        Scale an existing version of Deployment.
        Args:
            :param deployment_name: DeploymentConfig name
            :param replicas: scale up/down to this number
        """
        self.do_action("scale", ["--replicas=" + str(replicas), "dc", deployment_name])
        if replicas > 0:
            self._wait_for_deployment(deployment_name)

    def rsync(self, deployment_name: str, source: str, dest: str):
        """Copy files from remote pod container to local.

        First container in the pod from the specified deployment will be used.

        Note: For the time being, rsync is only available from remote to local.

        Args:
            :param deployment_name: DeploymentConfig name
            :param source: Remote file-path.
            :param dest: Local dir where the file will be copied to.
        """
        if not os.path.isdir(dest):
            raise ValueError("You must provide a valid local directory to 'dest'.")

        def select_pod(apiobject):
            annotation = "openshift.io/deployment-config.latest-version"
            lastest_version = apiobject.get_annotation(annotation)
            return apiobject.get_label("deployment") == f"{deployment_name}-{lastest_version}"

        pod = oc.selector("pods").narrow(select_pod).object().name()

        self.do_action("rsync", [f"{pod}:{source}", dest])

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
        self.do_action("rollout", ["status", deployment_name])

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
            :param source: The source of the template, it must be either an url or a path to a local file.
            :param params: The parameters to be passed to the source when building it.
        """
        opt_args = []
        if params:
            opt_args.extend([f"--param={n}={v}" for n, v in params.items()])

        if os.path.isfile(source):
            source = f"--file={source}"

        self.do_action("new-app", [source, opt_args])

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
            :param deployment_name: The deployment name.
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
