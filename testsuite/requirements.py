"""CommonConfiguration requirements"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from testsuite.certificates import CertificateManager

if TYPE_CHECKING:
    from testsuite.openshift.client import OpenShiftClient


# pylint: disable=too-few-public-methods
class OpenshiftRequirement(ABC):
    """Requires configured OpenShift servers and ability to choose which one to use"""
    @abstractmethod
    def openshift(self, server: Optional[str] = "default", project: Optional[str] = "threescale") -> "OpenShiftClient":
        """Creates OpenShiftClient for specific project on specific server"""


class CertificateManagerRequirement(ABC):
    """Requires configured certificate manager with ability to create new certificates"""
    @property
    @abstractmethod
    def manager(self) -> CertificateManager:
        """Certificate Manager"""


class ThreeScaleAuthDetails(ABC):
    """Requires configured 3scale url and token"""
    @property
    @abstractmethod
    def token(self) -> str:
        """Authorization token for 3scale"""

    @property
    @abstractmethod
    def url(self) -> str:
        """Url of 3scale"""
