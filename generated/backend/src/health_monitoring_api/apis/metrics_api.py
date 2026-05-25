# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from health_monitoring_api.apis.metrics_api_base import BaseMetricsApi
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
from datetime import datetime
from pydantic import Field, StrictStr
from typing import Optional
from typing_extensions import Annotated
from health_monitoring_api.models.error import Error
from health_monitoring_api.models.heart_rate_batch import HeartRateBatch
from health_monitoring_api.models.heart_rate_history_response import HeartRateHistoryResponse
from health_monitoring_api.models.heart_rate_ingestion_response import HeartRateIngestionResponse
from health_monitoring_api.models.temperature_history_response import TemperatureHistoryResponse
from health_monitoring_api.models.temperature_ingestion_response import TemperatureIngestionResponse
from health_monitoring_api.models.temperature_minute import TemperatureMinute
from health_monitoring_api.models.validation_error import ValidationError
from health_monitoring_api.security_api import get_token_ApiKeyAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/patients/{patient_id}/metrics/heart-rate",
    responses={
        200: {"model": HeartRateHistoryResponse, "description": "Heart rate history returned successfully."},
        400: {"model": Error, "description": "The request is syntactically valid JSON but semantically invalid for this operation."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        422: {"model": ValidationError, "description": "The request does not match the schema validation rules."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Metrics"],
    summary="Get heart rate history",
    response_model_by_alias=True,
)
async def get_heart_rate_history(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    start_time: Optional[datetime] = Query(None, description="Inclusive start of the time range, expressed as UTC ISO 8601 date-time.", alias="start_time"),
    end_time: Optional[datetime] = Query(None, description="Exclusive end of the time range, expressed as UTC ISO 8601 date-time.", alias="end_time"),
    limit: Optional[int] = Query(100, description="Maximum number of records returned.", alias="limit", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="Number of records skipped before returning results.", alias="offset", ge=0),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> HeartRateHistoryResponse:
    """Returns raw heart rate samples for one patient in the requested time range."""
    if not BaseMetricsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMetricsApi.subclasses[0]().get_heart_rate_history(patient_id, start_time, end_time, limit, offset)


@router.get(
    "/v1/patients/{patient_id}/metrics/temperature",
    responses={
        200: {"model": TemperatureHistoryResponse, "description": "Temperature history returned successfully."},
        400: {"model": Error, "description": "The request is syntactically valid JSON but semantically invalid for this operation."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        422: {"model": ValidationError, "description": "The request does not match the schema validation rules."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Metrics"],
    summary="Get temperature history",
    response_model_by_alias=True,
)
async def get_temperature_history(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    start_time: Optional[datetime] = Query(None, description="Inclusive start of the time range, expressed as UTC ISO 8601 date-time.", alias="start_time"),
    end_time: Optional[datetime] = Query(None, description="Exclusive end of the time range, expressed as UTC ISO 8601 date-time.", alias="end_time"),
    limit: Optional[int] = Query(100, description="Maximum number of records returned.", alias="limit", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="Number of records skipped before returning results.", alias="offset", ge=0),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> TemperatureHistoryResponse:
    """Returns one temperature value per minute for one patient."""
    if not BaseMetricsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMetricsApi.subclasses[0]().get_temperature_history(patient_id, start_time, end_time, limit, offset)


@router.post(
    "/v1/patients/{patient_id}/metrics/heart-rate",
    responses={
        201: {"model": HeartRateIngestionResponse, "description": "Heart rate batch accepted and stored."},
        400: {"model": Error, "description": "The request is syntactically valid JSON but semantically invalid for this operation."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        409: {"model": Error, "description": "The request conflicts with an existing resource."},
        422: {"model": ValidationError, "description": "The request does not match the schema validation rules."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Metrics"],
    summary="Ingest heart rate batch",
    response_model_by_alias=True,
)
async def ingest_heart_rate_batch(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    heart_rate_batch: HeartRateBatch = Body(..., description="Heart rate batch sampled at 10 Hz for exactly 60 seconds."),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> HeartRateIngestionResponse:
    """Stores a heart rate batch for one patient.  The batch represents exactly 60 seconds of heart rate data sampled at 10 Hz, therefore the request must contain exactly 600 values.  Individual sample timestamps are derived by the backend using:  &#x60;sample_timestamp &#x3D; start_timestamp + index / 10 seconds&#x60; """
    if not BaseMetricsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMetricsApi.subclasses[0]().ingest_heart_rate_batch(patient_id, heart_rate_batch)


@router.post(
    "/v1/patients/{patient_id}/metrics/temperature",
    responses={
        201: {"model": TemperatureIngestionResponse, "description": "Temperature value accepted and stored."},
        400: {"model": Error, "description": "The request is syntactically valid JSON but semantically invalid for this operation."},
        401: {"model": Error, "description": "Missing or invalid API key."},
        404: {"model": Error, "description": "The requested resource was not found."},
        409: {"model": Error, "description": "The request conflicts with an existing resource."},
        422: {"model": ValidationError, "description": "The request does not match the schema validation rules."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["Metrics"],
    summary="Ingest temperature minute",
    response_model_by_alias=True,
)
async def ingest_temperature_minute(
    patient_id: StrictStr = Path(..., description="Unique identifier of the patient."),
    temperature_minute: TemperatureMinute = Body(..., description="One temperature average value for a single minute."),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> TemperatureIngestionResponse:
    """Stores one aggregated body temperature value for one patient.  The timestamp must be aligned to a minute boundary. In practice this means seconds and sub-seconds should be zero. """
    if not BaseMetricsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMetricsApi.subclasses[0]().ingest_temperature_minute(patient_id, temperature_minute)
