"""dynaconf recommended way to setup setup"""

from dynaconf.base import LazySettings
from dynaconf.constants import DEFAULT_SETTINGS_FILES


# this was copied from dynaconf/__init__.py before it became deprecated
# pylint: disable=invalid-name
settings = LazySettings(
    environments=True,
    lowercase_read=True,
    load_dotenv=True,
    default_settings_paths=DEFAULT_SETTINGS_FILES,
)
