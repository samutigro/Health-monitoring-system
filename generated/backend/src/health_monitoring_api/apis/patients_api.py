# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from health_monitoring_api.apis.patients_api_base import BasePatientsApi
import impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from health_monitoring_api.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr
from typing import Any, Optional
from typing_extensions import Annotated
from health_monitoring_api.models.error import Error
from health_monitoring_api.models.patient import Patient
from health_monitoring_api.models.patient_create import PatientCreate
from health_monitoring_api.models.patient_list_response import PatientListResponse
from health_monitoring_api.models.patient_update import PatientUpdate
from health_monitoring_api.models.validation_error import ValidationError
from health_monitoring_api.security_api import get_token_ApiKeyAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/v1/patients",
    responses={
        201: {"model": Patient, "description": "Patient created successfully."},
        400: {"model": Error, "description": "The request is syntactically valid JSON but semantically invalid for this operation."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        422: {"model": ValidationError, "description": "The request does not match the schema validation rules."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Patients"],
    summary="Create patient",
    response_model_by_alias=True,
)
async def create_patient(
    patient_create: PatientCreate = Body(..., description="Patient data used to create a new patient."),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> Patient:
    """Creates a new patient profile."""
    if not BasePatientsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BasePatientsApi.subclasses[0]().create_patient(patient_create)


@router.delete(
    "/v1/patients/{patient_id}",
    responses={
        204: {"description": "Patient deleted successfully. The response body is empty."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Patients"],
    summary="Delete patient",
    response_model_by_alias=True,
)
async def delete_patient(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> None:
    """Deletes a patient and the associated biometric metrics."""
    if not BasePatientsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BasePatientsApi.subclasses[0]().delete_patient(patient_id)


@router.get(
    "/v1/patients/{patient_id}",
    responses={
        200: {"model": Patient, "description": "Patient returned successfully."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Patients"],
    summary="Get patient",
    response_model_by_alias=True,
)
async def get_patient(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> Patient:
    """Returns a patient profile by identifier."""
    if not BasePatientsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BasePatientsApi.subclasses[0]().get_patient(patient_id)


@router.get(
    "/v1/patients",
    responses={
        200: {"model": PatientListResponse, "description": "Patient list returned successfully."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Patients"],
    summary="List patients",
    response_model_by_alias=True,
)
async def list_patients(
    limit: Optional[int] = Query(100, description="Maximum number of records returned.", alias="limit", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="Number of records skipped before returning results.", alias="offset", ge=0),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> PatientListResponse:
    """Returns a paginated list of patient profiles."""
    if not BasePatientsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BasePatientsApi.subclasses[0]().list_patients(limit, offset)


@router.put(
    "/v1/patients/{patient_id}",
    responses={
        200: {"model": Patient, "description": "Patient updated successfully."},
        400: {"model": Error, "description": "The request is syntactically valid JSON but semantically invalid for this operation."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        422: {"model": ValidationError, "description": "The request does not match the schema validation rules."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Patients"],
    summary="Update patient",
    response_model_by_alias=True,
)
async def update_patient(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    patient_update: PatientUpdate = Body(..., description="Patient data used to update an existing patient."),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> Patient:
    """Replaces the editable fields of an existing patient profile."""
    if not BasePatientsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BasePatientsApi.subclasses[0]().update_patient(patient_id, patient_update)
