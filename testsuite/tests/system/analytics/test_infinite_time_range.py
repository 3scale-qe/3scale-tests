"""
System API allows for almost infinite time range when using usage endpoints,
which causes too much strain on the system and might result in 5xx

https://issues.redhat.com/browse/THREESCALE-6649

Warning: due to the nature of the problem, test might produce false negatives, but it is better than having nothing
"""

from datetime import datetime, timedelta, timezone

import pytest
from packaging.version import Version
from threescale_api.errors import ApiClientError

from testsuite import TESTED_VERSION

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6649"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.11"), reason="TESTED_VERSION < Version('2.11')"),
]


@pytest.fixture(scope="module")
def backends_mapping(backend):
    """Mapping our custom backend to the service"""
    return {"/": backend}


@pytest.fixture(scope="module")
def backend(custom_backend):
    """Our custom backend"""
    return custom_backend()


@pytest.mark.parametrize(
    "entity_type,entity",
    [
        pytest.param("backend_apis", "backend", id="Backend"),
        pytest.param("applications", "application", id="Application"),
        pytest.param("services", "service", id="Service"),
    ],
)
@pytest.mark.parametrize(
    "granularity, max_allowed_delta",
    [
        pytest.param("day", timedelta(weeks=52), id="day"),  # Maximum time range is 1 year
        # Maximum time range should be 1O years, it doesnt work yet
        pytest.param(
            "month",
            timedelta(weeks=52 * 10),
            id="month-10years",
            marks=[pytest.mark.xfail, pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7601")],
        ),
        pytest.param("month", timedelta(weeks=52 * 9), id="month-9years"),  # 9 years works
        pytest.param("hour", timedelta(days=89), id="hour"),  # Maximum time range is 90 days
    ],
)
# pylint: disable=too-many-arguments
def test_application_usage(api_client, request, entity_type, entity, granularity, max_allowed_delta, threescale):
    """Tests that usage endpoints wont fail when supplied with ridiculous date ranges"""
    # To have some usage data
    api_client().get("/test")
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    entity_id = request.getfixturevalue(entity)["id"]
    # pylint: disable=protected-access
    threescale.analytics._list_by_resource(
        resource_id=entity_id,
        resource_type=entity_type,
        period=None,
        since=yesterday.isoformat(),
        until=(yesterday + max_allowed_delta).isoformat(),
        granularity=granularity,
    )

    with pytest.raises(ApiClientError, match="400"):
        # pylint: disable=protected-access
        threescale.analytics._list_by_resource(
            resource_id=entity_id,
            resource_type=entity_type,
            period=None,
            since=yesterday.isoformat(),
            until="8000-09-19 23:49:00",
            granularity=granularity,
        )
