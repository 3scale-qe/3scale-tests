"""Module containing all basic gateways"""
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from weakget import weakget

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

    CAPABILITIES: List[Capability] = []

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

    CAPABILITIES = [Capability.APICAST]

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

    def on_service_create(self, service):
        try:
            if weakget(self).options.print_logs % False:
                if not hasattr(self, "_taillog"):
                    setattr(self, "_taillog", {})
                getattr(self, "_taillog")[service["name"]] = len(self.get_logs())
        except NotImplementedError:
            return

    def on_service_delete(self, service):
        try:
            if weakget(self).options.print_logs % False:
                # pylint: disable=protected-access
                cut = weakget(self)._taillog[service["name"]] % 0
                applog = self.get_logs()[cut:].lstrip()
                header = " %s log " % getattr(self, "name", "Unknown Gateway")
                if len(applog) > 0:
                    print("{:~^80}".format(header), file=sys.stderr)
                    print(applog, file=sys.stderr)
                    print("~" * 80, file=sys.stderr)
        except NotImplementedError:
            return
