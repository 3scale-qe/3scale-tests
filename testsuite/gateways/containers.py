"""Collection of gateways that run in containerized environment"""
from testsuite.gateways.apicast import SelfManagedApicast


class ContainerizedApicast(SelfManagedApicast):
    """
    Gateway intended for use with RHEL based Apicasts deployed in containerized environments
    For the time being its is functionally the same as SelfManagedApicast
    """

    def set_env(self, name: str, value):
        raise NotImplementedError()

    def get_env(self, name: str):
        raise NotImplementedError()

    def reload(self):
        raise NotImplementedError()
