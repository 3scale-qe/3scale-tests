"""Module containing all basic gateways"""

from abc import ABC, abstractmethod
from typing import Set, Type, TypeVar, Union

from testsuite.capabilities import Capability
from testsuite.configuration import SettingsParser
from testsuite.lifecycle_hook import LifecycleHook
from testsuite.openshift.env import Properties


class AbstractGateway(LifecycleHook, ABC):
    """Basic gateway for use with Apicast"""

    CAPABILITIES: Set[Capability] = set()
    HAS_PRODUCTION = False

    @property
    def environ(self) -> Properties:
        """Returns environ object for given gateway"""
        raise NotImplementedError()

    @abstractmethod
    def create(self):
        """Starts this gateway"""

    @abstractmethod
    def destroy(self):
        """Destroys gateway"""


Gateway = TypeVar("Gateway", bound=AbstractGateway)


def new_gateway(
    kinds: dict, settings_, kind: Union[Type[Gateway], str] = None, staging: bool = True, **kwargs
) -> Gateway:
    """Low-level function to initialize gateway of given type. Not to be used directly.

    Settings priority:
    1. Function arguments
    2. Settings block named after the class name (TemplateApicast)
    3. default settings block
    """
    configuration = settings_["default"].copy()
    clazz = kinds[kind] if isinstance(kind, str) else kind  # type: ignore
    if clazz is None:
        clazz = kinds[settings_["default"]["kind"]]

    if clazz.__name__ in settings_:
        configuration.update(settings_[clazz.__name__])
    configuration.update(kwargs)
    configuration["kind"] = clazz
    configuration["settings"] = settings_

    return SettingsParser().process(global_kwargs={"staging": staging}, **configuration)
