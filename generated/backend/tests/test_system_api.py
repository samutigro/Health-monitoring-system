# coding: utf-8

from fastapi.testclient import TestClient


from health_monitoring_api.models.error import Error  # noqa: F401
from health_monitoring_api.models.health_check import HealthCheck  # noqa: F401


def test_get_health(client: TestClient):
    """Test case for get_health

    Check API health
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/health",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

