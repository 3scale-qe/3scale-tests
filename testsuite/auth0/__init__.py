"""
Custom Auth0 resources for testsuite
"""
import http.client
import json

from testsuite.config import settings


def auth0_token():
    """
    Token for Auth0 API
    """
    auth = settings["auth0"]
    conn = http.client.HTTPSConnection(auth["domain"])
    payload = (
        "{" + f"\"client_id\":\"{auth['client']}\","
        f"\"client_secret\":\"{auth['client-secret']}\","
        f"\"audience\":\"https://{auth['domain']}/api/v2/\",\"grant_type\":\"client_credentials\"" + "}"
    )
    headers = {"content-type": "application/json"}
    conn.request("POST", "/oauth/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))["access_token"]
