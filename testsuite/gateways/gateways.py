"""Module containing all basic gateways"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Set

from testsuite.capabilities import Capability
from testsuite.lifecycle_hook import LifecycleHook
from testsuite.openshift.env import Environ
from testsuite.requirements import OpenshiftRequirement

if TYPE_CHECKING:
    from testsuite.openshift.client import OpenShiftClient


class GatewayRequirements(OpenshiftRequirement, ABC):
    """Requirements for running gateways"""

    @property
    @abstractmethod
    def staging(self) -> bool:
        """Returns if the current gateway is staging or production"""

    @property
    @abstractmethod
    def current_openshift(self) -> "OpenShiftClient":
        """Returns currently configured openshift"""


class AbstractGateway(LifecycleHook, ABC):
    """Basic gateway for use with Apicast"""

    CAPABILITIES: Set[Capability] = set()

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


class AbstractApicast(AbstractGateway, ABC):
    """Interface defining basic functionality of an Apicast gateway"""

    CAPABILITIES = {Capability.APICAST}

    @abstractmethod
    def reload(self):
        """Reloads gateway"""

    @abstractmethod
    def get_logs(self, since_time: Optional[datetime] = None) -> str:
        """Gets the logs of the active Apicast pod from specific time"""

    def create(self):
        pass

    def destroy(self):
        pass
