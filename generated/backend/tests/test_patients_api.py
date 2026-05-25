# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Any, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from health_monitoring_api.models.error import Error  # noqa: F401
from health_monitoring_api.models.patient import Patient  # noqa: F401
from health_monitoring_api.models.patient_create import PatientCreate  # noqa: F401
from health_monitoring_api.models.patient_list_response import PatientListResponse  # noqa: F401
from health_monitoring_api.models.patient_update import PatientUpdate  # noqa: F401
from health_monitoring_api.models.validation_error import ValidationError  # noqa: F401


def test_create_patient(client: TestClient):
    """Test case for create_patient

    Create patient
    """
    patient_create = {"name":"name","weight":241.09825,"profile_picture":"https://openapi-generator.tech","age":9}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/patients",
    #    headers=headers,
    #    json=patient_create,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_delete_patient(client: TestClient):
    """Test case for delete_patient

    Delete patient
    """

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "DELETE",
    #    "/v1/patients/{patient_id}".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_patient(client: TestClient):
    """Test case for get_patient

    Get patient
    """

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/patients/{patient_id}".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_list_patients(client: TestClient):
    """Test case for list_patients

    List patients
    """
    params = [("limit", 100),     ("offset", 0)]
    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/patients",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_update_patient(client: TestClient):
    """Test case for update_patient

    Update patient
    """
    patient_update = {"name":"name","weight":241.09825,"profile_picture":"https://openapi-generator.tech","age":9}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "PUT",
    #    "/v1/patients/{patient_id}".format(patient_id='550e8400-e29b-41d4-a716-446655440000'),
    #    headers=headers,
    #    json=patient_update,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

