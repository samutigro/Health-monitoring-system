# coding: utf-8

from fastapi.testclient import TestClient


from datetime import datetime  # noqa: F401
from pydantic import Field, StrictStr  # noqa: F401
from typing import Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from health_monitoring_api.models.error import Error  # noqa: F401
from health_monitoring_api.models.heart_rate_batch import HeartRateBatch  # noqa: F401
from health_monitoring_api.models.heart_rate_history_response import HeartRateHistoryResponse  # noqa: F401
from health_monitoring_api.models.heart_rate_ingestion_response import HeartRateIngestionResponse  # noqa: F401
from health_monitoring_api.models.temperature_history_response import TemperatureHistoryResponse  # noqa: F401
from health_monitoring_api.models.temperature_ingestion_response import TemperatureIngestionResponse  # noqa: F401
from health_monitoring_api.models.temperature_minute import TemperatureMinute  # noqa: F401
from health_monitoring_api.models.validation_error import ValidationError  # noqa: F401


def test_get_heart_rate_history(client: TestClient):
    """Test case for get_heart_rate_history

    Get heart rate history
    """
    params = [("start_time", '2025-08-01T10:00:00Z'),     ("end_time", '2025-08-01T11:00:00Z'),     ("limit", 100),     ("offset", 0)]
    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/patients/{patient_id}/metrics/heart-rate".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_temperature_history(client: TestClient):
    """Test case for get_temperature_history

    Get temperature history
    """
    params = [("start_time", '2025-08-01T10:00:00Z'),     ("end_time", '2025-08-01T11:00:00Z'),     ("limit", 100),     ("offset", 0)]
    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/patients/{patient_id}/metrics/temperature".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_ingest_heart_rate_batch(client: TestClient):
    """Test case for ingest_heart_rate_batch

    Ingest heart rate batch
    """
    heart_rate_batch = {"start_timestamp":"2000-01-23T04:56:07.000+00:00","samples":[45.215736,45.215736,45.215736,45.215736,45.215736]}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/patients/{patient_id}/metrics/heart-rate".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #    json=heart_rate_batch,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_ingest_temperature_minute(client: TestClient):
    """Test case for ingest_temperature_minute

    Ingest temperature minute
    """
    temperature_minute = {"value":34.640663,"timestamp":"2000-01-23T04:56:07.000+00:00"}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/patients/{patient_id}/metrics/temperature".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #    json=temperature_minute,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

