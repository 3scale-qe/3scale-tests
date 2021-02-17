"""
Rewrite spec/functional_specs/policies/url_rewrite_query/query_rewrite_policy_liquid_set_spec.rb
"""

from typing import Dict, List
from urllib.parse import urlparse
import pytest
from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def params():
    """
    Parameters p to create query arg commands, used in the liquid format of:
     {{ p }}
     """
    return ["remote_addr", "http_method", "uri", "host", "remote_addr"]


@pytest.fixture(scope="module")
def funcs():
    """
     Parameters p to create query arg commands, used in the liquid
     format of: {{ 1000 | p }}
    """
    return ["time", "localtime", "today", "now", "utctime", "cookie_time",
            "http_time"]


@pytest.fixture(scope="module")
def all_params(params, funcs):
    """
    Combined list of params + funcs, used in the test
    """
    return params + funcs


@pytest.fixture(scope="module")
def query_args_commands(params, funcs) -> List[Dict[str, str]]:
    """
    Creates list of query_args_commands used to configure the policy
    """
    commands = []

    for param in params:
        command = create_command_from_param(param, False)
        commands.append(command)

    for func in funcs:
        command = create_command_from_param(func, True)
        commands.append(command)

    # appends three commands without a distinct pattern
    commands.append({"op": "set", "arg": "normal_arg", "value": "value"})
    commands.append({"op": "set", "arg": "liquid_arg", "value_type": "liquid",
                     "value": "Service {{ service.id }}"})
    commands.append({"op": "set", "arg": "md5_uri", "value_type": "liquid",
                     "value": "{{ uri | md5 }}"})
    return commands


def create_command_from_param(param: str, is_func: bool) -> Dict[str, str]:
    """
    :param param
    :param is_func: if true the value for param p is '{{ 1000 | p }}
           else '{{ p }}
    :return: Command setting the policy in the form of a Dict
    """
    liquid_value = "{{ 1000 | " + param + " }}" if is_func else "{{ " + param + " }}"
    return {"op": "set", "arg": param, "value_type": "liquid", "value": liquid_value}


@pytest.fixture(scope="module")
def policy_settings(query_args_commands):
    """ Adds url query rewriting policy, configured using the query_args_commands """
    return rawobj.PolicyConfig("url_rewriting", {
        "query_args_commands": query_args_commands})


def test_query_rewrite_policy_liquid_set(api_client, service, all_params):
    """
    Test url query rewriting policy with args using liquid templates
        - Create commands describing how the url is going to be rewritten
            - For params p ("remote_addr", "http_method", "uri", "host", "remote_addr"),
              the liquid_value l_v is going to be {{ p }}
            - For funcs p ("time", "localtime", "today", "now", "utctime", "cookie_time",
              "http_time"), the liquid_value is going to be {{ 1000 | p }}
            - For both, the command is going to take form of:
              {"op": "set", "arg": p, "value_type": "liquid", "value": l_v}
            - Add three special commands
                - {"op": "set", "arg": "normal_arg", "value": "value"}
                - {"op": "set", "arg": "liquid_arg", "value_type": "liquid",
                     "value": "Service {{ service.id }}"}
                - <<{"op": "set", "arg": "md5_uri", "value_type": "liquid",
                     "value": "{{ uri | md5 }}"}
        - add the url_rewriting_policy, configure using the defined commands
        - make request to '/get' endpoint

    Test if:
        - response has status code 200
        - plaintext arg is added
        - service id liquid tag is added
        - uri liquid tag is added
        - md5 function is used on uri liquid
        - host is added to the liquid tag
        - http method liquid tag is added
        - for each parameter p, a liquid tag "#{p}" is added and it is not empty
    """

    response = api_client().get("/get")

    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    echoed_request_params = echoed_request.params
    parsed_url = urlparse(service.proxy.list()['sandbox_endpoint'])

    assert echoed_request_params["normal_arg"] == "value"
    assert echoed_request_params["liquid_arg"] == "Service " + str(service["id"])
    assert echoed_request_params["uri"] == "/get"
    assert echoed_request_params["md5_uri"] == "D3170460F7014C0475FF0723DEEFFD4B".lower()
    assert echoed_request_params["host"] == parsed_url.hostname
    assert echoed_request_params["http_method"] == "GET"

    for param in all_params:
        # Path should not be empty
        assert param in echoed_request_params
        # Argument should not be empty
        assert len(echoed_request_params[param]) != 0
