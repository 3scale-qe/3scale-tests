"""
Sets up gateway defined in testsuite settings
"""
import importlib
import inspect
import pkgutil
from typing import Type, TypeVar, Union

from testsuite.config import settings
from testsuite.configuration import SettingsParser
from testsuite.gateways.gateways import AbstractGateway

# walk through all sub-packages and import all gateway classes
__all__ = ["gateway", "default"]

Gateway = TypeVar("Gateway", bound=AbstractGateway)

for _, module, _ in pkgutil.walk_packages(__path__, "testsuite.gateways."):  # type: ignore
    imported = importlib.import_module(module)
    for item in dir(imported):
        if item not in __all__:
            obj = getattr(imported, item)
            if inspect.isclass(obj) and issubclass(obj, AbstractGateway):
                globals()[item] = obj
                __all__.append(item)


def load_type():
    """Loads currently selected global gateway"""
    return globals()[settings["threescale"]["gateway"]["default"]["kind"]]


# Best name would be type, but that is a function. I also oppose clazz
default = load_type()


# This could be written much more cleanly without specifying kind,
# but this version enables typing support if kind is a class
def gateway(kind: Union[Type[Gateway], str] = None, staging: bool = True, **kwargs) -> Gateway:
    """
    Return gateway instance of given kind
    Settings priority:
    1. Function arguments
    2. Settings block named after the class name (TemplateApicast)
    3. default settings block
    """
    configuration = settings["threescale"]["gateway"]["default"].copy()
    kind = kind or configuration["kind"]
    clazz = globals()[kind] if not inspect.isclass(kind) else kind  # type: ignore
    name = kind.__name__ if inspect.isclass(kind) else kind  # type: ignore

    named_settings = {}
    if name in settings["threescale"]["gateway"]:
        named_settings = settings["threescale"]["gateway"][name]

    configuration.update(named_settings)
    configuration.update(kwargs)
    configuration["kind"] = clazz

    return SettingsParser().process(global_kwargs={"staging": staging}, **configuration)
