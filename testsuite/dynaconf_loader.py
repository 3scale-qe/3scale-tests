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

from pathlib import Path
import logging
import os
import os.path

from packaging.version import Version, InvalidVersion

import yaml

from openshift import OpenShiftPythonException
from testsuite.openshift.client import OpenShiftClient


identifier = "threescale"  # pylint: disable=invalid-name
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def _route2url(route):
    """Convert host from openshift route to https:// url"""

    return f"https://{route['spec']['host']}"


def _testsuite_version():
    """Get testsuite version string"""

    path = os.path.join(Path(os.path.abspath(__file__)).parent, "VERSION")
    with open(path, encoding="utf8") as version:
        return version.read().strip()


def _guess_version(ocp):
    """Attempt to determine version from amp-system imagestream"""

    version = None
    lookup = _docker_image(ocp, "amp-system")

    try:
        version = lookup["name"]
        Version(version)
    except (KeyError, InvalidVersion):
        version = lookup["from"]["name"].split(":", 1)[1].replace("3scale", "")
        try:
            Version(version)
        except InvalidVersion:
            return _testsuite_version().split("-")[0]

    return str(version)


def _apicast_image(ocp):
    """Find source of amp-apicast image"""
    lookup = ocp.do_action("get", ["dc/apicast-production", "-o", "yaml"])
    lookup = yaml.safe_load(lookup.out())
    return lookup["spec"]["template"]["spec"]["containers"][0]["image"]


def _docker_image(ocp, name):
    """shared helper to get image object of specific name"""

    lookup = ocp.do_action("get", ["imagestream", name, "-o", "yaml"])
    lookup = yaml.safe_load(lookup.out())
    lookup = lookup["spec"]["tags"]

    return [i for i in lookup if i.get("from", {}).get("kind") == "DockerImage"][-1]


def _rhsso_password(server_url, token):
    """Search for SSO admin password"""
    try:
        # is this RHOAM?
        tools = OpenShiftClient(
            project_name="redhat-rhoam-user-sso", server_url=server_url, token=token)
        return tools.secrets["credential-rhssouser"]["ADMIN_PASSWORD"].decode("utf-8")
    except (OpenShiftPythonException, KeyError):
        try:
            # was it deployed as part of tools?
            tools = OpenShiftClient(
                project_name="tools", server_url=server_url, token=token)
            return tools.environ("sso")["SSO_ADMIN_PASSWORD"]
        except (OpenShiftPythonException, KeyError):
            return None


# pylint: disable=unused-argument,too-many-locals
def load(obj, env=None, silent=None, key=None):
    """Reads and loads in to "settings" a single key or all keys from vault

    :param obj: the settings instance
    :param env: settings env default='DYNACONF'
    :param silent: if errors should raise
    :param key: if defined load a single key, else load all in env
    :return: None
    """

    try:  # one large try/except block for now with logging at the end
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
        devel_url = _route2url(ocp.routes.for_service("system-developer")[0])
        superdomain = ocp.config_maps["system-environment"]["THREESCALE_SUPERDOMAIN"]
        try:
            backend_route = ocp.routes.for_service("backend-listener")[0]
        except IndexError:
            # RHOAM changed service name owning the route
            backend_route = ocp.routes.for_service("backend-listener-proxy")[0]
        catalogsource = "UNKNOWN"
        try:
            catalogsource = ocp.do_action("get", ["catalogsource", "-o=jsonpath={.items[0].spec.image}"]).out().strip()
        except OpenShiftPythonException:
            pass

        # all this or nothing
        if None in (project, admin_url, admin_token, master_url, master_token, devel_url):
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
                "superdomain": superdomain,
                "catalogsource": catalogsource,
                "admin": {
                    "url": admin_url,
                    "username": ocp.secrets["system-seed"]["ADMIN_USER"].decode("utf-8"),
                    "password": ocp.secrets["system-seed"]["ADMIN_PASSWORD"].decode("utf-8"),
                    "token": admin_token},
                "master": {
                    "url": master_url,
                    "username": ocp.secrets["system-seed"]["MASTER_USER"].decode("utf-8"),
                    "password": ocp.secrets["system-seed"]["MASTER_PASSWORD"].decode("utf-8"),
                    "token": master_token},
                "devel": {
                    "url": devel_url},
                "gateway": {
                    "default": {
                        "portal_endpoint": f"https://{admin_token}@3scale-admin.{superdomain}",
                        "image": _apicast_image(ocp),
                        "openshift": ocp
                    },
                    "TemplateApicast": {
                        "image": apicast_image,
                        "portal_endpoint": f"https://{admin_token}@3scale-admin.{superdomain}",
                        "openshift": ocp
                    },
                },
                "backend_internal_api": {
                    "route": backend_route,
                    "username": ocp.secrets["backend-internal-api"]["username"],
                    "password": ocp.secrets["backend-internal-api"]["password"]
                }
            },
            "rhsso": {
                "password": _rhsso_password(ocp_setup.get("server_url"), ocp_setup.get("token"))
            }}

        # this overwrites what's already in settings to ensure NAMESPACE is propagated
        project_data = {
            "openshift": {
                "projects": {
                    "threescale": {
                        "name": project}}}}

        settings.update(project_data)
        obj.update(data, loader_identifier=identifier)
        obj.update(settings)
        log.info("dynamic dynaconf loader successfully got data from openshift")
    except Exception as err:
        if silent:
            log.debug("'%s' appeared with message: %s", type(err).__name__, err, exc_info=True)
            return
        raise err
