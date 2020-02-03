# pylint: disable=missing-module-docstring
from packaging.version import Version

from dynaconf import settings

TESTED_VERSION = Version(str(settings["threescale"]["version"]))
