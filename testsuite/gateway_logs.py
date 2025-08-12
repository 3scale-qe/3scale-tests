"""Pytest plugin for collecting gateway logs"""

import logging
from datetime import datetime, timezone

import pytest
from _pytest.outcomes import Skipped

from testsuite.gateways.gateways import Capability

log = logging.getLogger(__name__)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item):
    """Figures out what gateways are in use and when did he test setup started"""
    start_time = datetime.now(timezone.utc)
    result = yield

    item.gateways = {}
    # If the test is skipped (by our other hook), rest of the hooks is still executed and fails
    if result.excinfo is not None and Skipped in result.excinfo:
        return
    # pylint: disable=protected-access
    request = item._request
    try:
        if "api_client" in request.fixturenames:
            item.gateways["staging_gateway"] = request.getfixturevalue("staging_gateway")
        if "prod_client" in request.fixturenames:
            item.gateways["production_gateway"] = request.getfixturevalue("production_gateway")

        _print_logs(item, start_time, "setup", "setup")
    except Exception as err:  # pylint: disable=broad-except
        log.debug("Can't access gateway logs because of %s", err)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    """Prints setup logs and figures out what gateways are in use and when did the test execution started"""
    # pylint: disable=protected-access
    start_time = datetime.now(timezone.utc)
    yield
    _print_logs(item, start_time, "call", "test-run")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_teardown(item):
    """Collect logs and add them to the output"""
    start_time = datetime.now(timezone.utc)
    yield
    _print_logs(item, start_time, "teardown", "teardown")


def _print_logs(item, start_time, phase, suffix):
    """Appends logs to the stdout"""
    # This cannot ever fail or it will cause chain reaction
    # https://github.com/pytest-dev/pytest/issues/7724
    try:
        for gateway_name, gateway in item.gateways.items():
            name = f" {gateway_name} ({suffix}) "
            if Capability.LOGS in gateway.CAPABILITIES:
                item.add_report_section(
                    phase, "stdout", _generate_log_section(name, gateway.get_logs(since_time=start_time))
                )
            else:
                item.add_report_section(
                    phase, "stdout", _generate_log_section(name, "Gateway doesn't have LOGS capability")
                )
    # pylint: disable=broad-except
    except Exception as exc:
        item.add_report_section(
            phase, "stderr", f"({suffix}) Exception encountered while getting gateway logs: {exc}\n"
        )


def _generate_log_section(name, content):
    """Generates log section"""
    header = "{:~^80}".format(name)
    footer = "~" * 80
    return "\n".join(text for text in (header, content, footer, "\n"))
