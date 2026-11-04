"""
Regression test for the developer portal "read-only field injection" fix.
"""

import re

import httpx
import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION

from testsuite.config import settings
from testsuite.utils import blame

pytestmark = [pytest.mark.nopersistence,
              pytest.mark.skipif(TESTED_VERSION < Version("2.15"), reason="TESTED_VERSION < Version('2.15')"),
              pytest.mark.issue("https://redhat.atlassian.net/browse/THREESCALE-11522"),
              ]

PASSWORD = "Abc$12345678"
INJECTED_VALUE = "Injected Internal Value"
WRITABLE_VALUE = "Writable Value"


def _authenticity_token(html):
    """Scrape the Rails CSRF token out of a developer portal page."""
    match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', html)
    assert match, "authenticity_token not found on developer portal page"
    return match.group(1)


def _field_key(field):
    """Form-encoded signup key for an Account- or User-target custom field."""
    if field["target"] == "Account":
        return f"account[{field['name']}]"
    return f"account[user][{field['name']}]"


def _signup(client, org_name, username, extra_fields):
    """
    Perform a developer-portal signup POST, exactly like the browser form would,
    additionally injecting ``extra_fields`` (form-encoded field name -> value)
    that are not part of the rendered form.
    """
    token = _authenticity_token(client.get("/signup").text)
    data = {
        "utf8": "✓",
        "authenticity_token": token,
        "_method": "post",
        "commit": "Sign up",
        "account[org_name]": org_name,
        "account[user][username]": username,
        "account[user][email]": f"{username}@example.com",
        "account[user][password]": PASSWORD,
        "account[user][password_confirmation]": PASSWORD,
        **extra_fields,
    }
    return client.post("/signup", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})


@pytest.fixture
def custom_field(threescale, request):
    """
    Factory creating a custom field definition (fields_definition) via the admin
    API. Each created field is deleted at the end of the test.
    """

    def _create(target, read_only=False, hidden=False):
        name = blame(request, "field").replace("-", "_")
        field = threescale.fields_definitions.create(
            {
                "target": target,
                "name": name,
                "label": name,
                "read_only": read_only,
                "hidden": hidden,
                "required": False,
            }
        )
        request.addfinalizer(lambda: threescale.fields_definitions.delete(field.entity_id))
        return field

    return _create


@pytest.fixture
def developer_portal(provider_account, testconfig):
    """
    Raw HTTP client pointed at the developer portal, already past the site
    access code gate (if the portal is protected by one).
    """
    base_url = settings["threescale"]["devel"]["url"]
    access_code = provider_account["site_access_code"]
    with httpx.Client(base_url=base_url, verify=testconfig["ssl_verify"], follow_redirects=True, timeout=30) as client:
        landing = client.get("/")
        if access_code and "access_code" in landing.text.lower():
            client.post(
                "/access_code",
                data={"access_code": access_code, "authenticity_token": _authenticity_token(landing.text)},
            )
        yield client


def test_signup_ignores_read_only_custom_fields(developer_portal, threescale, request, custom_field):
    """
    A developer-portal signup that injects read-only custom fields must create
    the account but ignore those field values, whether the field is hidden or
    visible, for both Account- and User-target fields.

    Preparation:
        - create read-only custom fields for every (target, hidden) combination:
          Account/User x hidden/visible
        - create a plain writable Account custom field (control)
    Test:
        - POST /signup on the developer portal injecting all fields
        - assert the account is created
        - assert the writable field WAS stored (proves the injection reaches the
          server, so the test cannot pass vacuously)
        - assert every read-only field was NOT stored
    """
    read_only_fields = [
        custom_field("Account", read_only=True, hidden=True),
        custom_field("Account", read_only=True, hidden=False),
        custom_field("User", read_only=True, hidden=True),
        custom_field("User", read_only=True, hidden=False),
    ]
    writable_account = custom_field("Account")

    org_name = blame(request, "org")
    username = blame(request, "user")

    extra_fields = {_field_key(field): INJECTED_VALUE for field in read_only_fields}
    extra_fields[_field_key(writable_account)] = WRITABLE_VALUE

    response = _signup(developer_portal, org_name, username, extra_fields)
    assert "/signup/success" in str(
        response.url
    ), f"developer portal signup did not succeed (status={response.status_code}, url={response.url})"

    account = threescale.accounts.find(params={"username": username})
    request.addfinalizer(account.delete)
    user = account.users.list()[0]

    def stored_value(field):
        entity = account.entity if field["target"] == "Account" else user.entity
        return entity.get(field["name"])

    # Control: a writable custom field submitted the same way IS stored.
    assert (
        stored_value(writable_account) == WRITABLE_VALUE
    ), "control writable field was not stored - the injected fields may not have reached the server"

    # Fix: every read-only field injected by a developer must be ignored.
    for field in read_only_fields:
        assert stored_value(field) in (None, ""), (
            f"read-only {field['target']} field '{field['name']}' "
            f"(hidden={field['hidden']}) was set via developer-portal signup: {stored_value(field)!r}"
        )
