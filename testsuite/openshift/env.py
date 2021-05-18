"""Module containing classes that manipulate deployment configs environment"""
import re
import logging
from typing import TYPE_CHECKING, Callable, Match, Dict

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from testsuite.openshift.client import OpenShiftClient


class EnvironmentVariable:
    """Class for working with pure environmental variable that is set directly"""
    pattern = r"(?P<name>.*)=(?P<value>.*)"

    def __init__(self, openshift: 'OpenShiftClient',
                 deployment: str,
                 match: Match,
                 environ: "Environ") -> None:
        self.name = match.group("name")
        self.match = match
        self.deployment = deployment
        self.openshift = openshift
        self.environ = environ

    def get(self):
        """Returns value for the environment variable"""
        return self.match.group("value")

    def set(self, value: str):
        """Sets value for the environment variable"""
        self.openshift.do_action("set", ["env", self.environ.resource_type, self.deployment, f"{self.name}={value}"])
        # pylint: disable=protected-access
        self.environ.wait_for_resource(self.deployment)

    def delete(self):
        """Removes environment variable"""
        self.openshift.do_action("set", ["env", self.environ.resource_type, self.deployment, f"{self.name}-"])
        self.environ.wait_for_resource(self.deployment)


class SecretEnvironmentVariable(EnvironmentVariable):
    """Class for working with environmental variable that is set from secret"""
    pattern = r"#\ (?P<name>.*)\ from\ secret\ (?P<secret>.*),\ key\ (?P<key>.*)"

    def __init__(self, openshift: 'OpenShiftClient', deployment: str, match: Match, environ: "Environ") -> None:
        super().__init__(openshift, deployment, match, environ)
        self.secret = match.group("secret")
        self.key = match.group("key")

    def get(self):
        return self.openshift.secrets[self.secret][self.key]

    def set(self, value: str):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()


class ConfigMapEnvironmentVariable(EnvironmentVariable):
    """Class for working with environment variable that is set from configmap"""
    pattern = r"#\ (?P<name>.*)\ from\ configmap\ (?P<config>.*),\ key\ (?P<key>.*)"

    def __init__(self, openshift: 'OpenShiftClient', deployment: str, match: Match, environ: "Environ") -> None:
        super().__init__(openshift, deployment, match, environ)
        self.config = match.group("config")
        self.key = match.group("key")

    def get(self):
        return self.openshift.config_maps[self.config][self.key]

    def set(self, value: str):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()


logger = logging.getLogger(__name__)


class Environ:
    """Contains all env variables for a specific deployment config"""
    types = [EnvironmentVariable, SecretEnvironmentVariable, ConfigMapEnvironmentVariable]

    def __init__(self, openshift: 'OpenShiftClient',
                 name: str,
                 wait_for_resource: Callable[[str], None],
                 resource_type: str) -> None:
        self.openshift = openshift
        self.deployment_name = name
        self.resource_type = resource_type
        self.wait_for_resource = wait_for_resource
        self.__envs = None

    @property
    def _envs(self):
        if self.__envs is None:
            self.refresh()
        return self.__envs

    def refresh(self):
        """Refreshes all the environment variables"""
        self.__envs = {}
        cmd_result = self.openshift.do_action("set", ["env", self.resource_type, self.deployment_name, "--list"])
        for line in cmd_result.out().split("\n"):
            for env_type in self.types:
                match_obj = re.match(env_type.pattern, line)
                if match_obj:
                    env = env_type(openshift=self.openshift,
                                   deployment=self.deployment_name,
                                   match=match_obj,
                                   environ=self)
                    self.__envs[env.name] = env
                    break

    def set_many(self, envs: Dict[str, str]):
        """Allow setting many envs at a time."""
        env_args = []
        for name, value in envs.items():
            env_args.append(f"{name}={value}")
            logger.info("Setting env %s=%s in %s", name, value, self.deployment_name)

        self.openshift.do_action("set", ["env", self.resource_type, self.deployment_name, env_args])
        self.wait_for_resource(self.deployment_name)

        # refresh envs on the next access to self._envs
        self.__envs = None

    def __getitem__(self, name):
        if name not in self._envs:
            raise KeyError(name)
        return self._envs[name].get()

    def __setitem__(self, name, value):
        if name in self._envs:
            self._envs[name].set(value)
        else:
            self.openshift.do_action("set", ["env", self.resource_type, self.deployment_name, f"{name}={value}"])
            self.wait_for_resource(self.deployment_name)

        logger.info("Setting env %s=%s in %s", name, value, self.deployment_name)

        self.__envs = None

    def __delitem__(self, name):
        if name not in self._envs:
            raise KeyError(name)

        self._envs[name].delete()
        self.__envs = None
