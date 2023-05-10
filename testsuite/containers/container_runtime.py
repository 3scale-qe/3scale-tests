"""
This module defines common interface for working with different container runtimes and provides
some helper classes for easier interaction
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from copy import deepcopy


class Container:  # pylint: disable=too-few-public-methods
    """Simple structure for holding basic information about container"""

    def __init__(self, cid: str, started: bool):
        self.cid = cid
        self.deleted = False
        self.started = started


class ContainerConfig:
    """Helper class for defining configuration for creating new container"""

    # pylint: disable=too-many-arguments, too-many-instance-attributes
    def __init__(
        self,
        image: str,
        tag: str = "latest",
        env: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        entrypoint: Optional[str] = None,
        cmd: Optional[List[str]] = None,
        detach: bool = True,
    ):
        """ports dict is in format: {container_port: host_port}"""
        self.image = image
        self.tag = tag
        self.env = env or {}
        self.ports = ports or {}
        self.volumes = volumes or {}
        self.entrypoint = entrypoint
        self.cmd = cmd or []
        self.detach = detach

    @property
    def image_repotag(self) -> str:
        """Returns image id string in format 'imagename:tag'"""
        return f"{self.image}:{self.tag}"

    def attach_volume(self, host_path: str, container_path: str, mode: str = None):
        """Makes host_path volume accessible from container at container_path"""
        self.volumes[host_path] = {"bind": container_path, "mode": mode or "Z"}

    def detach_volume(self, host_path: str):
        """Removes attached volume from config"""
        del self.volumes[host_path]

    def clone(self) -> "ContainerConfig":
        """Makes a deep copy of this container config"""
        return deepcopy(self)


class ContainerRuntime(ABC):
    """Abstract base ContainerRuntime class defining common interface for working with containers"""

    @abstractmethod
    def run(self, container_config: ContainerConfig) -> Container:
        """
        Creates and runs new container defined by container_config \n
        If image is not present on host it tries to automatically pull it
        """

    @abstractmethod
    def start(self, container: Container):
        """Starts created or stopped container"""

    @abstractmethod
    def stop(self, container: Container):
        """Stops running container"""

    @abstractmethod
    def delete_container(self, container: Container):
        """Deletes container on host"""

    @abstractmethod
    def logs(self, container: Container) -> str:
        """Returns container's logs as a string"""

    @abstractmethod
    def close(self):
        """Closes client in order to free resources"""
