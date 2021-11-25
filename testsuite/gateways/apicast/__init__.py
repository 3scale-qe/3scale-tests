"""Module containing all APIcast gateways"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from testsuite.capabilities import Capability
from testsuite.gateways import AbstractGateway


class AbstractApicast(AbstractGateway, ABC):
    """Interface defining basic functionality of an APIcast gateway"""

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
