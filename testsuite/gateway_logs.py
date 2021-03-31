"""Pytest plugin for collecting gateway logs"""
from datetime import datetime

import pytest
from weakget import weakget

from testsuite.config import settings
from testsuite.gateways.gateways import Capability

PRINT_LOGS = weakget(settings)["reporting"]["print_app_logs"] % True


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup(item):
    """Figures out what gateways are in use and when did he test setup started"""
    if not PRINT_LOGS:
        return

    _gather_data(item)


@pytest.hookimpl(trylast=True)
def pytest_runtest_call(item):
    """Prints setup logs and figures out what gateways are in use and when did the test execution started"""
    # pylint: disable=protected-access
    if not PRINT_LOGS:
        return

    if hasattr(item, "gateways") and hasattr(item, "start_time"):
        _print_logs(item, item.gateways, item.start_time, "setup", "setup")

    _gather_data(item)


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item):
    """Collect logs and add them to the output"""
    if not PRINT_LOGS:
        return

    if hasattr(item, "gateways") and hasattr(item, "start_time"):
        _print_logs(item, item.gateways, item.start_time, "teardown", "test-run")


def _gather_data(item):
    """Gathers gateways used and start_time"""
    # pylint: disable=protected-access
    request = item._request
    gateways = {}

    # Most of the time gateways are referenced indirectly through lifecycle hooks, so I have to detect them like this
    if "api_client" in request.fixturenames:
        gateways["staging_gateway"] = request.getfixturevalue("staging_gateway")
    if "prod_client" in request.fixturenames:
        gateways["production_gateway"] = request.getfixturevalue("production_gateway")
    item.start_time = datetime.utcnow()
    item.gateways = gateways


def _print_logs(item, gateways, start_time, phase, suffix):
    """Appends logs to the stdout"""
    # This cannot ever fail or it will cause chain reaction
    # https://github.com/pytest-dev/pytest/issues/7724
    try:
        for gateway_name, gateway in gateways.items():
            name = f"{gateway_name} - {suffix}"
            if Capability.LOGS in gateway.CAPABILITIES:
                item.add_report_section(phase,
                                        "stdout",
                                        _generate_log_section(name, gateway.get_logs(since_time=start_time)))
            else:
                item.add_report_section(phase,
                                        "stdout",
                                        _generate_log_section(name, "Gateway doesn't have LOGS capability"))
    # pylint: disable=broad-except
    except Exception:
        pass


def _generate_log_section(name, content):
    """Generates log section"""
    header = "{:~^80}".format(name)
    footer = "~" * 80
    return "\n".join(text for text in (header, content, footer, "\n"))
