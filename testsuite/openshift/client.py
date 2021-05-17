"""This module implements an openshift interface with openshift oc client wrapper."""

import enum
import json
from contextlib import ExitStack
import os
from datetime import timezone
from typing import List, Dict, Union, Any, Optional, Callable

import openshift as oc

from testsuite.openshift.crd.apimanager import APIManager
from testsuite.openshift.env import Environ
from testsuite.openshift.objects import Secrets, ConfigMaps, Routes

# There is indeed cyclic import but it should be negated by TYPE_CHECKING check
# pylint: disable=cyclic-import
from testsuite.openshift.scaler import Scaler


class ServiceTypes(enum.Enum):
    """Service types enum."""

    CLUSTER_IP = "clusterip"
    EXTERNAL_NAME = "externalname"
    LOAD_BALANCER = "loadbalancer"
    NODE_PORT = "nodeport"


class OpenShiftClient:
    """OpenShiftClient is an interface to the official OpenShift python
    client."""
    # pylint: disable=too-many-public-methods

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
    def is_operator_deployment(self):
        """
        True, if the said namespace contains at least one APIManager resource
        It is equivalent to 3scale being deployed by operator
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
            try:
                return len(oc.selector("apimanager").objects()) > 0
            # If cluster doesn't know APIManager resource
            except oc.OpenShiftPythonException:
                return False

    @property
    def api_manager(self):
        """Returns APIManager object responsible for this deployment"""
        with ExitStack() as stack:
            self.prepare_context(stack)
            return oc.selector("apimanager").objects(cls=APIManager)[0]

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

    @property
    def scaler(self):
        """Scaling interface for both template and operator deployments"""

        return Scaler(self)

    def environ(self, name: str,
                resource_type: Optional[str] = None,
                wait_for_resource: Optional[Callable[[str], None]] = None):
        """Dict-like access to environment variables
        Args:
            :param name: Name of the resource
            :param resource_type: The resource type. Ex.: deploymentconfig, deployment. Defaults to dc
            :param wait_for_resource: Callable that should be called to wait until the resource is ready
        """
        resource_type = resource_type or "dc"
        wait_for_resource = wait_for_resource or self._wait_for_deployment
        return Environ(openshift=self, name=name, resource_type=resource_type, wait_for_resource=wait_for_resource)

    def deployment_environ(self, name: str):
        """Dict-like access to environment variables of a deployment
        Args:
            :param name: Name of the resource
        """
        return self.environ(name, "deployment", self.wait_for_ready)

    def patch(self, resource_type: str, resource_name: str, patch, patch_type: str = None):
        """Patch the specified resource
        Args:
            :param resource_type: The resource type to be patched. Ex.: service, route, deploymentconfig
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

    def delete_app(self, app: str, resources: Optional[str] = None):
        """Removes resources belonging to certain application
        Args:
            :param resources: Types of resources to be deleted, defaults to "all"
            :param app: Application to be deleted
            """
        resources = resources or "all"
        self.do_action("delete", [resources, "-l", f"app={app}", "--ignore-not-found"])

    def delete_template(self, template: str, params: Dict[str, str] = None):
        """
        Deletes resources specified in the template after processing it with params
        oc process -f template --param KEY=VALUE --param ... | oc delete -f -
        :param template: template specifying the resources to delete
        :param params: params to process the template with
        """
        opt_args: List[Union[List, str]] = ["-f", template]

        if params:
            opt_args.extend([f"--param={n}={v}" for n, v in params.items()])
        processed_tmpl = json.loads(self.do_action('process', opt_args).actions().pop().out)

        for resource in processed_tmpl["items"]:
            self.delete(resource['kind'], resource['metadata']['name'])

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

        pod = self.get_pod(deployment_name).object().name()
        self.do_action("rsync", [f"{pod}:{source}", dest])

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

    # pylint: disable=too-many-arguments
    def add_volume(self, deployment_name: str, volume_name: str, mount_path: str,
                   secret_name: str = None, configmap_name: str = None):
        """Add volume to a given deployment.

        Args:
            :param deployment_name: The deployment name
            :param volume_name: The volume name
            :param mount_path: The path to be mounted
            :param secret_name: The name of an existing Secret
            :param configmap_name: The name of an existing ConfigMap
        """
        self._manage_volume("add", deployment_name, volume_name, mount_path, secret_name, configmap_name)

    def remove_volume(self, deployment_name: str, volume_name: str):
        """Remove volume from a given deployment.

        Args:
            :param deployment_name: The deployment name
            :param volume_name: The volume name
        """
        self._manage_volume("remove", deployment_name, volume_name)

    # pylint: disable=too-many-arguments
    def _manage_volume(self, action: str, deployment_name: str, volume_name: str,
                       mount_path: str = None, secret_name: str = None,
                       configmap_name: str = None):
        """Manage volumes for a given deployment.

        You can add or remove a volume by passing `add` or `remove` to :param action.

        Args:
            :param action: Either "add" or "remove" option
            :param deployment_name: The deployment name
            :param volume_name: The volume name
            :param mount_path: The path to be mounted
            :param secret_name: The name of an existing Secret
            :param configmap_name: The name of an existing ConfigMap
        """
        if secret_name and configmap_name:
            raise ValueError("You must use either Secret or ConfigMap, not both.")

        opt_args = ["--name", volume_name]
        if mount_path:
            opt_args.extend(["--mount-path", mount_path])

        if secret_name:
            opt_args.extend(["--secret-name", secret_name])

        if configmap_name:
            opt_args.extend(["--configmap-name", configmap_name])

        self.do_action("set", ["volume", f"dc/{deployment_name}", f"--{action}", opt_args])
        self._wait_for_deployment(deployment_name)

    def _wait_for_deployment(self, deployment_name: str):
        """Wait for a given deployment to be running.

        Args:
            :param deployment_name: The deployment name.
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
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

    def wait_for_ready(self, deployment_name: str):
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
            oc.selector(f"deployment/{deployment_name}").until_all(
                success_func=lambda deployment: "readyReplicas" in deployment.model.status
            )

    def get_logs(self, deployment_name: str, since_time=None, tail: int = -1) -> str:
        """
        Get merged logs for the pods of the most recent deployment

        Works only for DeploymentConfig, not for Deployment
        :param since_time starting time from logs
        :param deployment_name name of the pod to get the logs of
        :param tail: how many logs to get, defaults to all
        :return: logs of the pod
        """
        cmd_args = []
        if since_time is not None:
            d_with_timezone = since_time.replace(tzinfo=timezone.utc)
            time = d_with_timezone.isoformat()
            cmd_args.append(f"--since-time={time}")
        pod_selector = self.get_pod(deployment_name)
        logs = pod_selector.logs(tail, cmd_args=cmd_args)
        logs_merged = ""
        for key in logs:
            logs_merged += logs[key]
        return logs_merged

    def get_pod(self, deployment_name: str):
        """
        Gets the selector for the pods of the most recent deployment

        Works only for DeploymentConfig, not for Deployment
        :param deployment_name name of the pod to get
        :return: the pod of the most recent deployment
        """
        def select_pod(apiobject):
            annotation = "openshift.io/deployment-config.latest-version"
            latest_version = apiobject.get_annotation(annotation)
            return apiobject.get_label("deployment") == f"{deployment_name}-{latest_version}"

        return self.select_resource("pods", narrow_function=select_pod)

    def get_operator(self):
        """
        Gets the selector for the 3scale operator

        :return: the operator pod
        """
        def select_operator(apiobject):
            return apiobject.get_label("com.redhat.component-name") == "3scale-operator"

        return self.select_resource("pods", narrow_function=select_operator)

    def select_resource(self,
                        resource: str,
                        labels: Optional[Dict[str, str]] = None,
                        narrow_function: Optional[Callable[[oc.APIObject], bool]] = None):
        """
        Returns pods, that is filtered with narrow function
        :param resource: Resource to search
        :param labels: Labels to filter resources
        :param narrow_function: Optional filter that takes APIObject and returns true, if it should be selected
        :return: selector object with all selected pods
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
            if labels:
                selector = oc.selector(resource, labels=labels)
            else:
                selector = oc.selector(resource)

            if narrow_function:
                selector = selector.narrow(narrow_function)
            return selector

    def create(self, definition, cmd_args: Optional[List[str]] = None):
        """
        Creates objects from yaml/json representations

        :param definition: String yaml/json definition of the objects
        :param cmd_args: Optional list of command line arguments to pass to the command
        :return: Selector to match creates resources
        """
        with ExitStack() as stack:
            self.prepare_context(stack)
            return oc.create(definition, cmd_args)

    def create_service(self, name: str, service_type: ServiceTypes, port: int, target_port: int):
        """Create a new secret.
        Args:
            :param name: Service name
            :param service_type: Type of the service
            :param port: Port the service listens on
            :param target_port: Port to which the service forwards connections.
        """
        self.do_action("create", ["service", service_type.value, name, f"--tcp={port}:{target_port}"])

    def start_build(self, build_name):
        """
        Starts a build specified by the build_name
        """
        self.do_action("start-build", [build_name, "--wait=true"])

    def image_stream_tag(self, image_stream):
        """
        Gets the tag of the given imagestream
        """
        return self.do_action("get", ["imagestream", image_stream]).actions()[0].out.split()[7]
