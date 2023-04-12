"""This module implements an openshift interface with openshift oc client wrapper."""

import enum
from functools import cached_property
import json
import os
from contextlib import ExitStack
from typing import List, Dict, Union, Any, Optional, Callable, Sequence

import openshift as oc
import yaml

from testsuite.openshift.crd.apimanager import APIManager
from testsuite.openshift.deployments import KubernetesDeployment, DeploymentConfig, Deployment
from testsuite.openshift.objects import Secrets, ConfigMaps, Routes
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

    @cached_property
    def api_url(self):
        """Returns real API url"""
        with ExitStack() as stack:
            self.prepare_context(stack)
            return oc.whoami("--show-server=true")

    # pylint: disable=too-many-arguments
    def do_action(self, verb: str, cmd_args: Sequence[Union[str, Sequence[str]]] = None,
                  auto_raise: bool = True, parse_output: bool = False, no_namespace: bool = False):
        """Run an oc command."""
        cmd_args = cmd_args or []
        with ExitStack() as stack:
            self.prepare_context(stack)
            result = oc.invoke(verb, cmd_args, auto_raise=auto_raise, no_namespace=no_namespace)
            if parse_output:
                return oc.APIObject(string_to_model=result.out())
            return result

    @cached_property
    def project_exists(self):
        """Returns True if the project exists"""
        try:
            self.do_action("get", f"project/{self.project_name}")
            return True
        except oc.OpenShiftPythonException:
            return False

    @cached_property
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

    @cached_property
    def secrets(self):
        """Dict-like access to secrets"""

        return Secrets(self)

    @cached_property
    def routes(self):
        """Interface to access OpenShift routes"""

        return Routes(self)

    @cached_property
    def config_maps(self):
        """Dict-like access to config maps"""

        return ConfigMaps(self)

    @cached_property
    def scaler(self):
        """Scaling interface for both template and operator deployments"""

        return Scaler(self)

    def deployment(self, resource: str) -> Deployment:
        """Interface for deployment config manipulation"""
        if "/" not in resource:
            raise ValueError(f"Resource {resource} is not in <resource_type>/<name> format")
        resource_type = resource.split("/")[0]
        if resource_type in ("dc", "deploymentconfig"):
            return DeploymentConfig(self, resource)
        if resource_type == "deployment":
            return KubernetesDeployment(self, resource)
        raise ValueError(f"Resource type {resource_type} is unknown")

    def environ(self, name: str):
        """Dict-like access to environment variables
        Args:
            :param name: Name of the resource
        """
        return self.deployment(name).environ()

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

    def delete(self, resource_type: str, name: str, force: bool = False, ignore_not_found=False):
        """Delete a resource.
        Args:
            :param resource_type: The resource type to be deleted. Ex.: service, route, deploymentconfig
            :param name: The resource name
            :param force: Pass --force to oc delete
            :param ignore_not_found: If false, it will fail if the object doesn't exist
        """
        args = [f"--ignore-not-found={ignore_not_found}"]
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

    def new_app(self, source, params: Dict[str, str] = None):
        """Create application based on source code.

        Args:
            :param source: The source of the template, it must be either an url or a path to a local file.
            :param params: The parameters to be passed to the source when building it.
        """
        opt_args = []
        if params:
            opt_args.extend([f"--param={n}={v}" for n, v in params.items()])

        if os.path.isfile(source):
            source = f"--filename={source}"
        objects = self.do_action("process", [source, opt_args]).out()
        self.create(objects)

    def get_operator(self):
        """
        Gets the selector for the 3scale operator

        :return: the operator pod
        """
        def select_operator(apiobject):
            return apiobject.get_label("com.redhat.component-name") == "3scale-operator" \
                or apiobject.get_label("rht.subcomp") == "3scale_operator"

        return self.select_resource("pods", narrow_function=select_operator)

    def get_apicast_operator(self):
        """
        Gets the selector for the apicast operator

        :return: the operator pod
        """
        def select_operator(apiobject):
            return apiobject.get_label("com.redhat.component-name") == "apicast-operator" \
                or apiobject.get_label("rht.subcomp") == "apicast_operator"

        return self.select_resource("pods", narrow_function=select_operator)

    @property
    def apicast_operator_subscription(self):
        """
        Gets the selector for the apicast-operator subscription

        :return: the subscription
        """

        def select_operator(subscription):
            return subscription.model.spec.name == "apicast-operator"

        return self.select_resource("subscriptions", narrow_function=select_operator)

    @cached_property
    def has_apicast_operator(self):
        """True if apicast operator is found in local namespace or in openshift-operators"""
        try:
            return self.apicast_operator_subscription.object() is not None
        except oc.OpenShiftPythonException:
            ocp = OpenShiftClient("openshift-operators", self.server_url, self.token)
            try:
                return ocp.apicast_operator_subscription.object() is not None
            except oc.OpenShiftPythonException:
                return False

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
            selector = oc.selector(resource, labels=labels)

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

    def add_labels(self, name: str, object_type: str, labels: List[str]):
        """Add labels to the object.
        Args:
            :param name: Object name
            :param object_type: Type of the object
            :param labels: Labels to be added
        """
        params = [object_type, name]
        params.extend(labels)
        self.do_action("label", params)

    def start_build(self, build_name):
        """
        Starts a build specified by the build_name
        """
        self.do_action("start-build", [build_name, "--wait=true"])

    def image_stream_tag_from_trigger(self, name):
        """Gather tag from trigger of given obj name e.g. dc/something"""
        obj = self.do_action("get", [name, "-o", "yaml"], parse_output=True)
        for trigger in obj.model.spec.triggers:
            if trigger.type == "ImageChange":
                return trigger.imageChangeParams["from"]["name"].split(":", 1)[1]
        raise ValueError(f"{obj} without ImageChange trigger")

    def image_stream_tag(self, image_stream):
        """
        Gets the tag of the given imagestream
        """
        return self.do_action("get", ["imagestream", image_stream]).actions()[0].out.split()[7]

    def image_stream_repository(self, image_stream):
        """Returns absolute repository url for an image stream"""
        stream = self.do_action("get", ["imagestream", image_stream, "-o", "yaml"], parse_output=True)
        return stream.model.status.dockerImageRepository

    @cached_property
    def version(self):
        """Openshift Platform server version"""
        return oc.get_server_version()

    @cached_property
    def arch(self):
        """Openshift architecture"""
        lookup = self.do_action("cluster-info", ["dump", "-o", "yaml"], no_namespace=True)
        cluster_info = list(yaml.safe_load_all(lookup.out()))
        return cluster_info[0]["items"][0]["metadata"]["labels"]["kubernetes.io/arch"]
