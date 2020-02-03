"""This module contains basic objects for working with openshift resources """
from io import StringIO
import base64
import yaml


# pylint: disable=too-few-public-methods
class YAMLDataObject:
    """Dict-like interface to generic openshift resource yaml"""

    def __init__(self, client: "OpenShiftClient", resource_name: str):  # noqa: F821
        self._client = client
        self._resource_name = resource_name

    def __getitem__(self, name):
        """Return requested resource in yaml format"""

        return yaml.load(
            StringIO(self._client.do_action("get", [self._resource_name, name, "-o", "yaml"]).out()),
            Loader=yaml.FullLoader)["data"]


# pylint: disable=too-few-public-methods
class Secrets(YAMLDataObject):
    """Dict-like interface to openshift secrets"""

    def __init__(self, client: "OpenShiftClient"):  # noqa: F821
        super().__init__(client, "secret")

    def __getitem__(self, name: str):
        """Return requested secret in yaml format"""

        # pylint: disable=too-few-public-methods
        class _DecodedSecrets:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, name):
                return base64.b64decode(self._data[name])

        return _DecodedSecrets(super().__getitem__(name))


# pylint: disable=too-few-public-methods
class ConfigMaps(YAMLDataObject):
    """Dict-like interface to openshift secrets"""

    def __init__(self, client: "OpenShiftClient"):  # noqa: F821
        super().__init__(client, "cm")
