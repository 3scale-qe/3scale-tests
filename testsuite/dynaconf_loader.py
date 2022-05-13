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
from weakget import weakget

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
    try:
        version = ocp.image_stream_tag_from_trigger("dc/apicast-production")
        Version(version)
    except (ValueError, IndexError, OpenShiftPythonException, InvalidVersion):
        return ".".join(_testsuite_version().split(".")[:2])

    return str(version)


def _guess_apicast_operator_version(ocp):
    """Attempt to determine version of apicast operator from subscription"""

    version = None
    try:
        version = ocp.apicast_operator_subscription.object().model.status.installedCSV.split(".v")[1]
        version = version.split("-")[0]
        Version(version)
    except (ValueError, IndexError, OpenShiftPythonException, InvalidVersion):
        # returning value that is greater than any apicast version
        # in result all tests for latest apicast operator will run
        return "50035350"  # doesn't have to be spot at first glance, this is literal transcript of word "devel"

    return str(version)


def _apicast_image(ocp):
    """Find source of amp-apicast image"""
    lookup = ocp.do_action("get", ["dc/apicast-production", "-o", "yaml"])
    lookup = yaml.safe_load(lookup.out())
    return lookup["spec"]["template"]["spec"]["containers"][0]["image"]


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
            # first RHSSO 7.5 way
            return tools.secrets["credential-sso"]["ADMIN_PASSWORD"].decode("utf-8")
        except (OpenShiftPythonException, KeyError):
            try:
                # try 7.4 known deployment if previous fails
                return tools.environ("dc/sso")["SSO_ADMIN_PASSWORD"]
            except (OpenShiftPythonException, KeyError):
                return None


def _apicast_ocp(ocp, settings):
    """apicast operator can live in different namespace and even openshift"""
    settings = weakget(settings)["threescale"]["gateway"]["OperatorApicast"]["openshift"] % {}
    # the assumption is that patterns "3scale-{IDENTIFIER}" and "apicast-{IDENTIFIER}" are used
    maybe_project_name = ocp.project_name.replace("3scale", "apicast", 1)

    if not settings.get("project_name"):
        maybe_ocp = OpenShiftClient(
            project_name=maybe_project_name,
            server_url=settings.get("server_url"),
            token=settings.get("token"))
        if maybe_ocp.project_exists:
            return maybe_ocp

    return OpenShiftClient(
        project_name=settings.get("project_name"),
        server_url=settings.get("server_url"),
        token=settings.get("token"))


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

        apicast_ocp = _apicast_ocp(ocp, obj)

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
                "apicast_operator_version": _guess_apicast_operator_version(apicast_ocp),
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
                        "openshift": ocp
                    },
                    "TemplateApicast": {
                        "image": _apicast_image(ocp),
                    },
                    "OperatorApicast": {
                        "openshift": {
                            "project_name": apicast_ocp.project_name
                        }
                    },
                    "WASMGateway": {
                        "backend_host": backend_route["spec"]["host"]
                    }
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
