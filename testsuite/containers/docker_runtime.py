"""
This module contains everything what is needed for Docker implementation of ContainerRuntime
Depends on docker library
"""

from docker import DockerClient
from testsuite.containers.container_runtime import Container, ContainerRuntime, ContainerConfig


class DockerRuntime(ContainerRuntime):
    """ Docker implementation of ContainerRuntime """
    def __init__(self, uri: str):
        super().__init__()
        self._client = DockerClient(base_url=uri, version="auto", tls=False)

    def logs(self, container: Container) -> str:
        return self._client.containers.get(container.cid).logs()

    def delete_container(self, container: Container):
        self._client.containers.get(container.cid).remove(force=True)
        container.deleted = True

    def start(self, container: Container):
        self._client.containers.get(container.cid).start()
        container.started = True

    def stop(self, container: Container):
        self._client.containers.get(container.cid).stop(timeout=10)
        container.started = False

    def run(self, container_config: ContainerConfig) -> Container:
        container = self._client.containers.run(
            image=container_config.image_repotag,
            command=container_config.cmd,
            environment=container_config.env,
            entrypoint=container_config.entrypoint,
            detach=container_config.detach,
            ports=container_config.ports,
            volumes=container_config.volumes
        )

        return Container(container.id, started=True)

    def close(self):
        self._client.close()
