"""This module contains basic objects for working with openshift resources"""

import base64
import enum
import math
import typing
from io import StringIO
from typing import List, Union

import yaml

from testsuite.certificates import Certificate

if typing.TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class SecretKinds(enum.Enum):
    """Secret kinds enum."""

    TLS = "tls"
    GENERIC = "generic"
    DOCKER_REGISTRY = "docker-registry"


class SecretTypes(enum.Enum):
    """Secret types enum."""

    OPAQUE = "opaque"
    BASIC_AUTH = "kubernetes.io/basic-auth"
    TLS = "kubernetes.io/ssl"


class RemoteMapping:
    """Dict-like interface to generic yaml object"""

    def __init__(self, client: "OpenShiftClient", resource_name: str):
        self._client = client
        self._resource_name = resource_name

    def do_action(self, verb: str, cmd_args: List[Union[str, List[str]]] = None, auto_raise: bool = True):
        """Executes command and returns output in yaml format"""
        cmd_args = cmd_args or []
        cmd_args.extend(["-o", "yaml"])
        return yaml.load(StringIO(self._client.do_action(verb, cmd_args, auto_raise).out()), Loader=yaml.FullLoader)

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

    class Types(enum.Enum):
        """Route types enum."""

        EDGE = "edge"
        PASSTHROUGH = "passthrough"
        REENCRYPT = "reencrypt"

    def __init__(
        self,
        client,
    ) -> None:
        super().__init__(client, "route")

    def expose(self, name, service, hostname):
        """Expose containers internally as services or externally via routes.
        Returns requested route in yaml format.
        """
        return self._client.do_action("expose", ["service", service, f"--hostname={hostname}", f"--name={name}"])

    def create(self, name: str, route_type: "Types" = Types.EDGE, **kwargs):
        """Expose containers externally via secured routes
        Args:
            :param route_type: the route type available in Route.Types
            :param kwargs: options for the command
            :return Created route object
        """
        cmd_args = [f"--{k}={v}" for k, v in kwargs.items()]
        cmd_args.append("--output=json")
        return self._client.do_action("create", ["route", route_type.value, name, cmd_args], parse_output=True)

    def for_service(self, service) -> list:
        """
        Return routes for specific service
        It will sort results by 3scale.net/tenant_id label
        Usage: getting routes for admin portal, master portal...
        :param service: service name in OpenShift
        :return: list of routes
        """
        routes = [r for r in self if r["spec"]["to"]["name"] == service]
        routes = list(
            sorted(routes, key=lambda x: float(x["metadata"]["labels"].get("3scale.net/tenant_id", math.inf)))
        )
        return routes


class Secrets(RemoteMapping):
    """Dict-like interface to openshift secrets"""

    def __init__(self, client: "OpenShiftClient"):
        super().__init__(client, "secret")

    def __getitem__(self, name: str):
        """Return requested secret in yaml format"""

        # pylint: disable=too-few-public-methods
        class _DecodedSecrets:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, name):
                return base64.b64decode(self._data[name])

            def __contains__(self, name):
                return name in self._data

        return _DecodedSecrets(super().__getitem__(name)["data"])

    # pylint: disable=too-many-arguments
    def create(
        self,
        name: str,
        kind: SecretKinds = SecretKinds.GENERIC,
        secret_type: SecretTypes = None,
        string_data: typing.Dict[str, str] = None,
        files: typing.Dict[str, str] = None,
        certificate: Certificate = None,
        labels: typing.Dict[str, str] = None,
    ):
        """Create a new secret.

        Args:
            :param name: Secret name
            :param kind: The kind of the secret, given by SecretKinds
            :param secret_type: The type of the secret, given by SecretTypes
            :param string_data: Specify a key and literal value to insert in secret
            :param files: Key files key be specified using their file path,  in which case a default
                          name will be given to them, or optionally with a name and file path,
                          in which case the given name will be used.  Specifying a directory will
                          iterate each named file in the directory that is a valid secret key.
            :param certificate: The Certificate
            :param labels: Labels which are set to new object
        """
        opt_args = []

        if secret_type:
            opt_args.extend(["--type", secret_type.value])

        if string_data:
            opt_args.extend([f"--from-literal={n}={v}" for n, v in string_data.items()])

        if files:
            opt_args.extend([f"--from-file={n}={v}" for n, v in files.items()])

        if kind == SecretKinds.TLS:
            if certificate is None:
                raise ValueError("Certificate is required for TLS secret.")
            opt_args.extend(["--cert", certificate.files["certificate"], "--key", certificate.files["key"]])

        self.do_action("create", ["secret", kind.value, name, opt_args])
        if labels:
            for key, val in labels.items():
                self.do_action("label", ["secret/" + name, f"{key}={val}"])


class ConfigMaps(RemoteMapping):
    """Dict-like interface to openshift secrets"""

    def __init__(self, client: "OpenShiftClient"):
        super().__init__(client, "cm")

    def __getitem__(self, name):
        return super().__getitem__(name)["data"]

    def __setitem__(self, name, value):
        raise NotImplementedError()

    def add(self, name, literals: typing.Dict[str, str] = None):
        """Add new ConfigMap.

        Args:
            :param name: ConfigMap name.
            :param literals: Speficy a key and literal value to insert in config map.
        """
        cmd_args = []

        if literals:
            cmd_args.extend([f"--from-literal={n}={v}" for n, v in literals.items()])

        self.do_action("create", [self._resource_name, name, *cmd_args])
