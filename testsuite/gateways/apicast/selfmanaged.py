"""Self-managed APIcast already deployed somewhere in OpenShift """
import inspect
import logging
from typing import Union, Type

from weakget import weakget

from testsuite.capabilities import Capability
from testsuite.gateways.gateways import Gateway, new_gateway
from testsuite.gateways.apicast import AbstractApicast, OpenshiftApicast
from testsuite.openshift.client import OpenShiftClient

LOGGER = logging.getLogger(__name__)


class NoSuitableApicastError(Exception):
    """Raised if no deployment method is found"""


# pylint: disable=too-many-instance-attributes
class SelfManagedApicast(AbstractApicast):
    """Gateway for use with already deployed self-managed APIcast in OpenShift

    This is a "special" class behaving bit more dynamically during
    instantiation. Actually it can return instance of different class (never
    returns self in fact). It returns instance of OpenshiftApicast subclass
    that fits to the definition and/or environment. Due to this behavior
    specific criteria have to be met.
    """

    CAPABILITIES = {Capability.APICAST,
                    Capability.CUSTOM_ENVIRONMENT,
                    Capability.PRODUCTION_GATEWAY,
                    Capability.LOGS,
                    Capability.JAEGER}
    HAS_PRODUCTION = True

    # pylint: disable=unused-argument
    def __new__(cls, staging: bool, openshift: OpenShiftClient, settings,
                force: Union[Type[Gateway], str] = None, **kwargs):
        """
        :param force: The class to use can be defined explicitly
        """
        if cls is SelfManagedApicast:
            kind = force
            subclasses = OpenshiftApicast.__subclasses__()
            if isinstance(kind, str):
                for subclass in subclasses:
                    if subclass.__name__ == kind:
                        kind = subclass  # type: ignore
                        break

            def _openshift(subclass):
                """get right openshift for a subclass"""
                custom = weakget(settings)[subclass.__name__]["openshift"] % None
                if not custom:
                    return openshift
                if isinstance(custom, OpenShiftClient):
                    return custom
                return OpenShiftClient(
                        custom.get("project_name"), custom.get("url"), custom.get("token"))

            if not kind:
                candidates = sorted([i for i in subclasses if i.fits(_openshift(i))], key=lambda x: x.PRIORITY)
                if len(candidates):
                    kind = candidates[-1]  # type: ignore
            if kind:
                LOGGER.info("Chosen: %s", kind)
                classes = {i.__name__: i for i in subclasses}
                return new_gateway(classes, settings, kind, staging, **kwargs)
            raise NoSuitableApicastError()
        return super().__new__(cls)

    # pylint: disable=unused-argument
    def __init__(self, staging: bool, openshift: OpenShiftClient, settings,
                 force: Union[Type[Gateway], str] = None, **kwargs):
        raise TypeError("SelfManagedApicast should be never created actually")

    @classmethod
    def expected_init_args(cls):
        """Collect all the init parameters from cls and its subclasses"""
        expected = set(inspect.signature(cls.__new__).parameters.keys())
        for subclass in OpenshiftApicast.__subclasses__():
            expected.update(inspect.signature(subclass.__init__).parameters.keys())
        return list(expected - {'self', 'kwargs'})
