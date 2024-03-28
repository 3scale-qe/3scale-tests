# pylint: disable=invalid-name
"These are constructors to create native 3scale API objects"

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from threescale_api import resources


def PolicyConfig(name: str, configuration: dict, version: str = "builtin", enabled: bool = True) -> dict:
    """Creates policy config to be passed to API to policy chain
    Args:
        :param name: Policy name as known by 3scale
        :param version: Version of policy; default: 'builtin'
        :param enabled: Whether policy should be enabled; default: True
        :param configuration: a dict with configuration or particular policy"""
    return {"name": name, "version": version, "enabled": enabled, "configuration": configuration}


# pylint: disable=unused-argument
def Proxy(credentials_location: str = "query") -> dict:
    """builder of params to create a service proxy
    Args:
        :param credentials_location: Where to expected credentials; default 'query'"""
    return locals()


# pylint: disable=unused-argument
def Metric(system_name: str, friendly_name: str = None, unit: str = "hit"):
    """Builder of hash of parameters for to define metric
    Args:
        :param system_name: Name of metric
        :param friendly_name: Metric friendly name; by default equals to system_name
        :param unit: Measured unit of the metric; default: hit"""

    if friendly_name is None:
        friendly_name = system_name
    return locals()


# pylint: disable=unused-argument
def Method(system_name: str, friendly_name: str = None, unit: str = "hit"):
    """Bulder of params to create method used by service

    Args:
        :param system_name: Name ot the method
        :param friendly_name: User friendly name; by default equals to system_name
        :param unit: Measured unit of the method; default: hit"""

    if friendly_name is None:
        friendly_name = system_name
    # pylint: disable=possibly-unused-variable
    name = system_name
    return locals()


# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
def Mapping(
    metric: dict,
    pattern: str = "/",
    http_method: str = "GET",
    delta: int = 1,
    last: str = "false",
    position: int = None,
):
    """Builder of parameters to create Mapping
    Args:
        :param metric: Metric to be mapped
        :param pattern: URL pattern to map; deafult: /
        :param http_method: Method to map; default: GET
        :param delta: Incremental unit; default: 1
        :param last: If true, no other rules will be processed after
                     matching this one; default: false
        :param position: position in list of mapping rules"""

    metric_id = metric["id"]  # pylint: disable=possibly-unused-variable
    del metric
    if position is None:
        del position
    return locals()


def Application(
    name: str,
    application_plan: "resources.ApplicationPlan",
    description: str = None,
    account: "resources.Account" = None,
) -> dict:
    """builder of params to create an application
    Args:
        :param name: name of the application
        :param account: the owner of the application
        :param application_plan: ApplicationPlan linked with this application
        :param description: Descriptive text for the application"""
    if description is None:
        description = f"application {name}"

    obj = {
        "name": name,
        "plan_id": application_plan["id"],
        "description": description,
        "service_id": application_plan.service["id"],
    }

    if account is not None:
        obj["account_id"] = account["id"]

    return obj


def ApplicationPlan(
    name: str,
    approval_required: bool = False,
    state_event: str = "publish",
    service: "resources.Service" = None,
    setup_fee=0,
) -> dict:
    """builder of params to create an application plan
    Args:
        :param name: name of the plan
        :param service: The Service associated with this plan
        :approval_required: Is explicit manual approval needed? Default: False
        :state_event: initial state of the plan; default: 'publish'
        :param setup_fee: option for paid plan; default: 0"""
    obj = {"name": name, "approval_required": approval_required, "state_event": state_event, "setup_fee": setup_fee}

    if service is not None:
        obj["service_id"] = service["id"]

    return obj


def AccessToken(name: str, permission: str, scopes: List[str]):
    """Builder of params to create a new Personal AccessToken
    Args:
        :param name: the name of the access token
        :param permission: "ro" or "rw"
        :param scopes: array of scopes for new access token
    """
    obj = {"name": name, "permission": permission, "scopes": scopes}

    return obj


def CustomTenant(username: str, password: str = None, org_name: str = None, email: str = "anything@invalid.invalid"):
    """Builder of params to create a new tenant
    Args:
        :param username: the username of the tenant
        :param password: the password of the tenant
        :param orgname: If the orgname is not set username is used (backward compatibility)
    """
    if not org_name:
        org_name = username
    if not password:
        del password
    return locals()


# pylint: disable=too-many-arguments
def ActiveDoc(
    name: str,
    body: str,
    description: str = "",
    service: Optional["resources.Service"] = None,
    published: bool = True,
    skip_swagger_validations: bool = False,
) -> dict:
    """
    builder of params to create an active doc.
    Args:
        :param name: name of the plan
        :param service: The Service associated with this active doc
        :param body: Active doc. content
        :param description: description
        :param published: should it be published?
        :param skip_swagger_validations: should skip validation?
    """
    obj = {
        "name": name,
        "body": body,
        "description": description,
        "published": published,
        "skip_swagger_validations": skip_swagger_validations,
    }

    if service is not None:
        obj["service_id"] = service["id"]

    return obj


def Account(org_name: str, monthly_billing_enabled: bool, monthly_charging_enabled: bool) -> dict:
    """builder of params to create an account
    Args:
        :param org_name: name of the organization
        :param monthly_billing_enabled: Is monthly billing enabled?
        :param monthly_charging_enabled: Is monthly charging enabled?
    """
    tmp = {
        "org_name": org_name,
        "monthly_billing_enabled": monthly_billing_enabled,
        "monthly_charging_enabled": monthly_charging_enabled,
    }

    return {k: v for k, v in tmp.items() if v is not None}


def AccountUser(username: str, email: str, password: str) -> dict:
    """builder of params to create an account user
    Args:
        :param username: name
        :param email: email
        :param password: password
    """
    obj = {"username": username, "email": email, "password": password}

    return obj


def ApiDocParams(token: str, params: dict = None) -> dict:
    """builder of params for endpoints in API Docs
    Args:
        :param token: access_token
        :param params: dict of params defined in api endpoint
    """
    obj = {"access_token": token}
    if params:
        obj.update(params)

    return obj
