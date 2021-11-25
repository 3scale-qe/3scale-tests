"""Module containing all basic gateways"""
from abc import ABC, abstractmethod
from typing import Set

from testsuite.capabilities import Capability
from testsuite.lifecycle_hook import LifecycleHook
from testsuite.openshift.env import Environ


class AbstractGateway(LifecycleHook, ABC):
    """Basic gateway for use with Apicast"""

    CAPABILITIES: Set[Capability] = set()
    HAS_PRODUCTION = False

    @property
    def environ(self) -> Environ:
        """Returns environ object for given gateway"""
        raise NotImplementedError()

    @abstractmethod
    def create(self):
        """Starts this gateway"""

    @abstractmethod
    def destroy(self):
        """Destroys gateway"""
