"""
Custom loader for dynaconf

Some values can be gathered from openshift deployment of 3scale from relevant
configmaps, secrets, routes, etc. These values should be used as
default/fallback in case they aren't defined in config or by env variables.

dynaconf provides interface to custom loader that can be used to gather these
data and have them still available through settings object of dynaconf. It also
provides possibility to set the order oc loaders, this has some limitations
though.

The order of core loaders seems fixed, so custom loader can't be prepended to
them. Anyway this loader requires the config as it needs to know where to find
openshift deployment. That's true for both files and env loader (order of env
loader is defined in config/.env file). At same moment this has to be
overwritten by values from config and env. Therefore the update at the end of
load() is doubled.
"""

import os

from packaging.version import Version, InvalidVersion

import yaml

from testsuite.openshift.client import OpenShiftClient


identifier = "threescale"  # pylint: disable=invalid-name


def _route2url(route):
    """Convert host from openshift route to https:// url"""

    return f"https://{route['spec']['host']}"


def _guess_version(ocp):
    """Attempt to determine version from amp-system imagestream"""

    version = None
    lookup = _docker_image(ocp, "amp-system")

    try:
        version = lookup["name"]
        Version(version)
    except (KeyError, InvalidVersion):
        version = lookup["from"]["name"].split(":", 1)[1].replace("3scale", "")
        Version(version)

    return str(version)


def _apicast_image(ocp):
    """Find source of amp-apicast image"""

    return _docker_image(ocp, "amp-apicast")["from"]["name"]


def _docker_image(ocp, name):
    """shared helper to get image object of specific name"""

    lookup = ocp.do_action("get", ["imagestream", name, "-o", "yaml"])
    lookup = yaml.safe_load(lookup.out())
    lookup = lookup["spec"]["tags"]

    return [i for i in lookup if i.get("from", {}).get("kind") == "DockerImage"][0]


# pylint: disable=unused-argument
def load(obj, env=None, silent=None, key=None):
    """Reads and loads in to "settings" a single key or all keys from vault

    :param obj: the settings instance
    :param env: settings env default='DYNACONF'
    :param silent: if errors should raise
    :param key: if defined load a single key, else load all in env
    :return: None
    """

    # openshift project: if not set use ENV_FOR_DYNACONF, env NAMESPACE overwrites everything
    project = obj.get("env_for_dynaconf")
    project = obj.get("openshift", {}).get("projects", {}).get("threescale", {}).get("name", project)
    project = os.environ.get("NAMESPACE", project)

    ocp_setup = obj.get("openshift", {}).get("servers", {}).get("default", {})

    ocp = OpenShiftClient(
        project_name=project,
        server_url=ocp_setup.get("server_url"),
        token=ocp_setup.get("token"))

    admin_url = _route2url(ocp.routes.for_service("system-provider")[0])
    admin_token = ocp.secrets["system-seed"]["ADMIN_ACCESS_TOKEN"].decode("utf-8")
    master_url = _route2url(ocp.routes.for_service("system-master")[0])
    master_token = ocp.secrets["system-seed"]["MASTER_ACCESS_TOKEN"].decode("utf-8")

    # all this or nothing
    if None in (project, admin_url, admin_token, master_url, master_token):
        return

    # Values gathered in this loader are just fallback defaults, current
    # settings needs to be dumped and written again, because a) it doesn't seem
    # to be possible to change order of builtin loaders to make this one first;
    # b) values from file(s) are needed here anyway. Therefore dump & update
    settings = obj.to_dict()

    data = {
        "openshift": {
            "projects": {
                "threescale": {
                    "name": project}},
            "servers": {
                "default": {
                    "server_url": ocp.do_action("whoami", ["--show-server"]).out().strip()}}},
        "threescale": {
            "version": _guess_version(ocp),
            "superdomain": ocp.config_maps["system-environment"]["THREESCALE_SUPERDOMAIN"],
            "admin": {
                "url": admin_url,
                "token": admin_token},
            "master": {
                "url": master_url,
                "token": master_token},
            "gateway": {
                "template": "3scale-gateway",
                "image": _apicast_image(ocp),
                "type": "apicast",
                "configuration": {
                    "staging_deployment": "apicast-staging",
                    "production_deployment": "apicast-production"}}}}

    # this overwrites what's already in settings to ensure NAMESPACE is propagated
    project_data = {
        "openshift": {
            "projects": {
                "threescale": {
                    "name": project}}}}

    settings.update(project_data)
    obj.update(data, loader_identifier=identifier)
    obj.update(settings)
