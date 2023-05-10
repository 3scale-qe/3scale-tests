"""Module containing Deployment related classes"""
import os
import typing
from abc import ABC, abstractmethod
from contextlib import ExitStack
from datetime import timezone

import openshift as oc
from testsuite.openshift.env import Environ

if typing.TYPE_CHECKING:
    from testsuite.openshift.client import OpenShiftClient


class Deployment(ABC):
    """Common class for KubernetesDeployments and DeploymentConfigs,
    enables functionality that works on both to be written once"""

    def __init__(self, openshift: "OpenShiftClient", resource) -> None:
        super().__init__()
        self.openshift = openshift
        self.resource = resource
        split = resource.split("/")
        self.resource_type = split[0]
        self.name = split[1]

    def scale(self, replicas: int):
        """
        Scale an existing version of Deployment.
        Args:
            :param replicas: scale up/down to this number
        """
        self.openshift.do_action("scale", ["--replicas", str(replicas), self.resource])
        if replicas > 0:
            self.wait_for()

    def environ(self) -> Environ:
        """Dict-like access to environment variables"""
        return Environ(self)

    def rsync(self, source: str, dest: str):
        """Copy files from remote pod container to local.

        First container in the pod from the specified deployment will be used.

        Note: For the time being, rsync is only available from remote to local.

        Args:
            :param source: Remote file-path.
            :param dest: Local dir where the file will be copied to.
        """
        if not os.path.isdir(dest):
            raise ValueError("You must provide a valid local directory to 'dest'.")

        pod = self.get_pods().object().name()
        self.openshift.do_action("rsync", [f"{pod}:{source}", dest])

    def get_replicas(self):
        """
        Return number of replicas of Deployment
        """
        with ExitStack() as stack:
            self.openshift.prepare_context(stack)
            selector = oc.selector(self.resource)
            deployment = selector.objects()[0]
            return deployment.model.spec.replicas

    # pylint: disable=too-many-arguments
    def add_volume(self, volume_name: str, mount_path: str, secret_name: str = None, configmap_name: str = None):
        """Add volume to a given deployment.

        Args:
            :param volume_name: The volume name
            :param mount_path: The path to be mounted
            :param secret_name: The name of an existing Secret
            :param configmap_name: The name of an existing ConfigMap
        """
        self._manage_volume("add", volume_name, mount_path, secret_name, configmap_name)

    def remove_volume(self, volume_name: str):
        """Remove volume from a given deployment.

        Args:
            :param volume_name: The volume name
        """
        self._manage_volume("remove", volume_name)

    # pylint: disable=too-many-arguments
    def _manage_volume(
        self, action: str, volume_name: str, mount_path: str = None, secret_name: str = None, configmap_name: str = None
    ):
        """Manage volumes for a given deployment.

        You can add or remove a volume by passing `add` or `remove` to :param action.

        Args:
            :param action: Either "add" or "remove" option
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

        self.openshift.do_action("set", ["volume", self.resource, f"--{action}", opt_args])
        self.wait_for()

    def get_logs(self, since_time=None, tail: int = -1) -> str:
        """
        Get merged logs for the pods of the most recent deployment

        :param since_time starting time from logs
        :param tail: how many logs to get, defaults to all
        :return: logs of the pod
        """
        cmd_args = []
        if since_time is not None:
            d_with_timezone = since_time.replace(tzinfo=timezone.utc)
            time = d_with_timezone.isoformat()
            cmd_args.append(f"--since-time={time}")
        with ExitStack() as stack:
            self.openshift.prepare_context(stack)
            pod = self.get_pods()
            # For some reason, the logs can return empty string sometimes, this seems to mitigate it
            pod.objects()
            logs = pod.logs(tail, cmd_args=cmd_args)
        return "".join(logs.values())

    def patch(self, patch, patch_type: str = None, timeout=90):
        """Patches the deployment and waits until it is applied"""
        self.openshift.patch(self.resource_type, self.name, patch, patch_type)
        self.wait_for(timeout)

    def delete(self):
        """Deletes deployment"""
        self.openshift.delete(self.resource_type, self.name)

    def __str__(self) -> str:
        return self.resource

    @abstractmethod
    def rollout(self):
        """Rollouts (=redeploys) new configuration"""

    @abstractmethod
    def wait_for(self, timeout: int = 90):
        """Waits until all the replicas are ready"""

    @abstractmethod
    def get_pods(self):
        """Returns Selector for all pods for Deployment"""


class KubernetesDeployment(Deployment):
    """Pure Kubernetes deployment"""

    def __init__(self, openshift: "OpenShiftClient", resource: "str") -> None:
        super().__init__(openshift, resource)

    def rollout(self):
        self.openshift.do_action("delete", ["pod", "--force", "--grace-period=0", "-l", f"deployment={self.name}"])
        self.wait_for()

    def wait_for(self, timeout: int = 90):
        with ExitStack() as stack:
            self.openshift.prepare_context(stack)
            stack.enter_context(oc.timeout(timeout))
            oc.selector(self.resource).until_all(
                success_func=lambda deployment: "readyReplicas" in deployment.model.status
            )

    def get_pods(self):
        """Kubernetes Deployment doesnt have a nice universal way how to get the correct pods,
        so this method relies on pods having the deployment label"""
        return self.openshift.select_resource("pods", labels={"deployment": self.name})


class DeploymentConfig(Deployment):
    """OpenShift DeploymentConfig object"""

    def __init__(self, openshift: "OpenShiftClient", resource: str) -> None:
        super().__init__(openshift, resource)

    def rollout(self):
        self.openshift.do_action("rollout", ["latest", self.resource])
        self.openshift.do_action("rollout", ["status", self.resource])

    def wait_for(self, timeout: int = 90):
        self.openshift.do_action("rollout", ["status", f"--timeout={timeout}s", self.resource])

    def get_pods(self):
        def select_pod(apiobject):
            latest_version = apiobject.get_annotation("openshift.io/deployment-config.latest-version")
            return apiobject.get_label("deployment") == f"{self.name}-{latest_version}"

        return self.openshift.select_resource("pods", narrow_function=select_pod)
