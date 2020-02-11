"""This module contains basic objects for working with openshift resources """
import math
from io import StringIO
import base64
import typing
from typing import List, Union

import yaml

if typing.TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class RemoteMapping:
    """Dict-like interface to generic yaml object"""

    def __init__(self, client: 'OpenShiftClient', resource_name: str):
        self._client = client
        self._resource_name = resource_name

    def do_action(self, verb: str, cmd_args: List[Union[str, List[str]]] = None,
                  auto_raise: bool = True):
        """Executes command and returns output in yaml format"""
        cmd_args = cmd_args or []
        cmd_args.extend(["-o", "yaml"])
        return yaml.load(
            StringIO(self._client.do_action(verb, cmd_args, auto_raise).out()),
            Loader=yaml.FullLoader)

    def __iter__(self):
        """Return iterator for requested resource"""
        data = self.do_action("get", [self._resource_name])
        return iter(data["items"])

    def __getitem__(self, name):
        """Return requested resource in yaml format"""

        res = self.do_action("get", [self._resource_name, name, "--ignore-not-found=true"])
        if res is None:
            raise KeyError()
        return res

    def __contains__(self, name):
        res = self.do_action("get", [self._resource_name, name, "--ignore-not-found=true"])
        return res is not None

    def __delitem__(self, name):
        if name not in self:
            raise KeyError()
        self._client.do_action("delete", [self._resource_name, name])


class Routes(RemoteMapping):
    """Dict-like interface to OpenShift routes"""

    def __init__(self, client,) -> None:
        super().__init__(client, "route")

    def create(self, name, service, hostname):
        """Return requested route in yaml format"""
        return self._client.do_action("expose", ["service", service, f"--hostname={hostname}", f"--name={name}"])

    def for_service(self, service) -> list:
        """
        Return routes for specific service
        It will sort results by 3scale.net/tenant_id label
        Usage: getting routes for admin portal, master portal...
        :param service: service name in OpenShift
        :return: list of routes
        """
        routes = [r for r in self if r["spec"]["to"]["name"] == service]
        routes = list(sorted(routes,
                             key=lambda x: float(x["metadata"]["labels"].get("3scale.net/tenant_id", math.inf))))
        return routes


class Secrets(RemoteMapping):
    """Dict-like interface to openshift secrets"""

    def __init__(self, client: 'OpenShiftClient'):
        super().__init__(client, "secret")

    def __getitem__(self, name: str):
        """Return requested secret in yaml format"""

        # pylint: disable=too-few-public-methods
        class _DecodedSecrets:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, name):
                return base64.b64decode(self._data[name])

        return _DecodedSecrets(super().__getitem__(name)["data"])


class ConfigMaps(RemoteMapping):
    """Dict-like interface to openshift secrets"""

    def __init__(self, client: 'OpenShiftClient'):
        super().__init__(client, "cm")

    def __getitem__(self, name):
        return super().__getitem__(name)["data"]
