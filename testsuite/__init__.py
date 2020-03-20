# pylint: disable=missing-module-docstring
from dynaconf import settings

from packaging.version import Version
from testsuite.configuration import CommonConfiguration

TESTED_VERSION = Version(str(settings["threescale"]["version"]))
CONFIGURATION: CommonConfiguration = CommonConfiguration()
