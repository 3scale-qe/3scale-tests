# flake8: noqa F811
"""Tests that TLS Termination can be correctly setup from UI,
flake8 ignore needed because it treats the imported fixtures as F811 'redefiniton of unused..'"""

import pytest
import requests
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj
from testsuite.capabilities import Capability

# Imports for TLS fixtures
# noqa # pylint: disable=unused-import
from testsuite.tests.apicast.policy.tls.conftest import (
    certificate,
    create_cert,
    gateway_environment,
    gateway_options,
    manager,
    mount_certificate_secret,
    require_openshift,
    server_authority,
    staging_gateway,
    superdomain,
    valid_authority,
)
from testsuite.ui.views.admin.product.integration.configuration import (
    ProductConfigurationView,
)
from testsuite.ui.views.admin.product.integration.policies import (
    ProductPoliciesView,
    TlsTerminationPolicyView,
)
from testsuite.utils import blame

pytestmark = [
    pytest.mark.sandbag,  # TLS requires pretty specific complex setup
    pytest.mark.skipif(TESTED_VERSION < Version("2.11"), reason="TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6390"),
    pytest.mark.usefixtures("login"),
]


@pytest.fixture(scope="function")
def client(policy_application):
    """Returns HttpClient instance with retrying feature skipped."""
    api_client = policy_application.api_client(disable_retry_status_list={503, 404})
    # This won't work with Httpx but will save us about 10 mins for this test alone
    api_client.session = requests.Session()
    return api_client


@pytest.fixture(scope="function")
def policy_service(request, backends_mapping, custom_service, service_proxy_settings, lifecycle_hooks):
    """Preconfigured service with backend with scope for 1 test due to harmful changes on policy chain"""
    return custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )


@pytest.fixture(scope="function")
def policy_application(policy_service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Application for for api calls with changed policy chain"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), policy_service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    policy_service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def local_certs(request, certificate, mount_certificate_secret):
    """Sets ups certs located on APIcast"""

    def _setup(tls_policy_view):
        path = f'/var/run/secrets/{blame(request, "tls-term")}'
        mount_certificate_secret(path, certificate)
        tls_policy_view.add_local_certs(path)

    return _setup


@pytest.fixture(scope="module")
def embedded_certs(certificate):
    """Sets ups certs from filesystem"""

    def _setup(tls_policy_view):
        tls_policy_view.add_embedded_certs(certificate)

    return _setup


# pylint: disable=too-many-arguments
@pytest.mark.parametrize(
    "cert_type_setup",
    [
        pytest.param("local_certs", id="Local certificates", marks=pytest.mark.required_capabilities(Capability.OCP3)),
        pytest.param("embedded_certs", id="Embedded certificates"),
    ],
)
def test_tls_terminology_policy_via_ui(
    request, policy_service, navigator, cert_type_setup, client, valid_authority, policy_application
):
    """
    Test:
        - Create service via API
        - Navigate to Policies page and add TLS Termination policy
        - Add certificates to TLS termination policy
        - Assert that TLS termination policy is applied to API calls

    """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)

    policies_page.add_policy(TlsTerminationPolicyView.NAME)
    assert policies_page.policy_section.has_item(TlsTerminationPolicyView.NAME)
    policies_page.policy_section.edit_policy(TlsTerminationPolicyView.NAME)

    request.getfixturevalue(cert_type_setup)(policies_page.tls_termination_policy_view)
    policies_page.update_policy_chain_button.click()
    configuration_page = navigator.navigate(ProductConfigurationView, product=policy_service)
    configuration_page.configuration.staging_promote_btn.click()

    api_client = policy_application.api_client(verify=valid_authority.files["certificate"])
    api_client.session = requests.Session()
    assert api_client.get("/get").status_code == 200

    with pytest.raises(Exception, match="certificate verify failed: unable to get local issuer certificate"):
        client.get("/get")


def test_tls_terminology_policy_content(navigator, policy_service):
    """
    Test:
        - Create service via API
        - Navigate to Policies page and add TLS Termination policy
        - Assert that fields are correctly displayed for local or embedded option
    """
    policies_page = navigator.navigate(ProductPoliciesView, product=policy_service)

    policies_page.add_policy(TlsTerminationPolicyView.NAME)
    assert policies_page.policy_section.has_item(TlsTerminationPolicyView.NAME)

    policies_page.policy_section.edit_policy(TlsTerminationPolicyView.NAME)
    tls_policy_view = policies_page.tls_termination_policy_view
    tls_policy_view.add_cert_btn.click()
    tls_policy_view.cert_type_select.select_by_value("0")
    assert tls_policy_view.local_cert.is_displayed
    assert tls_policy_view.local_cert_key.is_displayed

    tls_policy_view.cert_type_select.select_by_value("1")
    assert tls_policy_view.embedded_cert.is_displayed
    assert tls_policy_view.embedded_cert_key.is_displayed

    tls_policy_view.cert_type_select.select_by_value("0")
    assert tls_policy_view.local_cert_key.is_displayed
    assert tls_policy_view.local_cert.is_displayed
