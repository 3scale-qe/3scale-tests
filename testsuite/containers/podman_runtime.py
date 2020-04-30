"""
This module contains everything what is needed for Podman implementation of ContainerRuntime
Depends on podman library
"""

from podman import ImageNotFound
from podman.client import Client

from testsuite.containers.container_runtime import ContainerRuntime, ContainerConfig, Container


class PodmanRuntime(ContainerRuntime):
    """ Podman implementation of ContainerRuntime """

    def __init__(self, remote_uri: str, identity_file: str = "~/.ssh/id_master", uri: str = "unix:/tmp/podman.sock"):
        super().__init__()
        self._client = Client(uri=uri, remote_uri=remote_uri, identity_file=identity_file)

    def run(self, container_config: ContainerConfig) -> Container:
        try:
            img = self._client.images.get(container_config.image_repotag)
        except ImageNotFound:
            self._client.images.pull(container_config.image_repotag)
            img = self._client.images.get(container_config.image_repotag)

        container = img.container(
            command=container_config.cmd,
            entrypoint=container_config.entrypoint,
            env=[f"{k}={v}" for k, v in container_config.env.items()],
            detach=True,
            publish=[f"{host}:{cont}" for cont, host in container_config.ports.items()],
            volume=[f"{host}:{cont['bind']}:{cont['mode']}" for host, cont in container_config.volumes.items()]
        ).start()

        return Container(container.id, started=True)

    def start(self, container: Container):
        self._client.containers.get(container.cid).start()
        container.started = True

    def stop(self, container: Container):
        self._client.containers.get(container.cid).stop(timeout=10)
        container.started = False

    def delete_container(self, container: Container):
        self._client.containers.get(container.cid).remove(force=True)
        container.deleted = True

    def logs(self, container: Container) -> str:
        return "".join(self._client.containers.get(container.cid).logs())

    def close(self):
        # should be done automatically by podman library
        # but it is not, it creates for every PodmanRuntime one ssh tunnel which persists till end of the process
        pass
