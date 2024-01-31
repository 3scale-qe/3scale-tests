"""Module responsible for processing configuration"""

import inspect
from typing import Dict, Any, Mapping

from weakget import weakget

from testsuite.config import settings
from testsuite.capabilities import Singleton
from testsuite.openshift.client import OpenShiftClient


def openshift(server="default", project="threescale") -> OpenShiftClient:
    """Creates OpenShiftClient for project"""
    project_name = weakget(settings)["openshift"]["projects"][project]["name"] % project

    try:
        server = settings["openshift"]["servers"][server]
    except KeyError:
        server = {}

    return OpenShiftClient(
        project_name=project_name, server_url=server.get("server_url", None), token=server.get("token", None)
    )


def call(method, **kwargs):
    """Calls method with only parameters it requires"""
    if hasattr(method, "expected_init_args"):
        expected = method.expected_init_args()
    else:
        expected = inspect.signature(method.__init__).parameters.keys()
    return method(**{k: v for k, v in kwargs.items() if k in expected})


class SettingsParser(metaclass=Singleton):
    """
    Parses settings into objects
    """

    def __init__(self) -> None:
        super().__init__()
        self.kinds: Dict[str, Any] = {}

    def register_kind(self, provider, kind: str = None):
        """Register new Kind"""
        if inspect.isclass(provider):
            kind = provider.__name__
        self.kinds[kind] = provider  # type: ignore

    def process(self, kind, global_kwargs=None, **kwargs):
        """
        Processes the kwargs and returns instantiated class
        :param kind: Str representation or kind or a Class
        :param global_kwargs: Arguments that will be passed to every kind regardless of depth,
        used for parametrized kinds
        :param kwargs: Arguments to be processed
        :return: Instantiated class
        """
        global_kwargs = global_kwargs or {}
        if inspect.isclass(kind) or inspect.isfunction(kind):
            method = kind
        else:
            method = self.kinds[kind]

        # process dicts
        processed_kwargs = {**global_kwargs}
        for key, value in kwargs.items():
            if isinstance(value, Mapping) and "kind" in value:
                processed_kwargs[key] = self.process(**value, global_kwargs=global_kwargs)
            else:
                processed_kwargs[key] = value
        return call(method, **processed_kwargs)


SettingsParser().register_kind(provider=OpenShiftClient)
