"""
Sets up gateway defined in testsuite settings
"""
import importlib
import inspect
import logging
import pkgutil
from typing import Type, Union

from testsuite.config import settings
from testsuite.gateways.gateways import AbstractGateway, Gateway, new_gateway

log = logging.getLogger(__name__)

# walk through all sub-packages and import all gateway classes
__all__ = ["gateway", "default", "Gateway"]

for _, module, _ in pkgutil.walk_packages(__path__, "testsuite.gateways."):  # type: ignore
    imported = importlib.import_module(module)
    for item in dir(imported):
        if item not in __all__:
            obj = getattr(imported, item)
            if inspect.isclass(obj) and issubclass(obj, AbstractGateway):
                globals()[item] = obj
                __all__.append(item)

# Best name would be type, but that is a function. I also oppose clazz
default = globals()[settings["threescale"]["gateway"]["default"]["kind"]]


# This could be written much more cleanly without specifying kind,
# but this version enables typing support if kind is a class
def gateway(kind: Union[Type[Gateway], str] = default, staging: bool = True, **kwargs) -> Gateway:
    """
    Return gateway instance of given kind
    Settings priority:
    1. Function arguments
    2. Settings block named after the class name (TemplateApicast)
    3. default settings block
    """
    log.info("Creating gateway(kind=%s, staging=%s, kwargs=%s)", kind, staging, kwargs)
    return new_gateway(globals(), settings["threescale"]["gateway"], kind, staging, **kwargs)
