from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import HeartRateSampleRecord, TemperatureSampleRecord
from app.routers.patients import parse_patient_id, patient_not_found
from app.schemas import (
    Error,
    HeartRateBatch,
    HeartRateHistoryResponse,
    HeartRateIngestionResponse,
    MetricSample,
    Pagination,
    TemperatureHistoryResponse,
    TemperatureIngestionResponse,
    TemperatureMinute,
    ValidationErrorResponse,
    ensure_utc,
)
from app.security import require_api_key
from app.validation import reject_unknown_query_params

router = APIRouter(prefix="/v1/patients/{patient_id}/metrics", tags=["Metrics"])


def bad_request(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "BAD_REQUEST", "message": message},
    )


def duplicate_metric() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "DUPLICATE_METRIC",
            "message": "A metric for this patient and timestamp already exists.",
        },
    )


def sample_to_schema(sample: TemperatureSampleRecord | HeartRateSampleRecord) -> MetricSample:
    return MetricSample(timestamp=sample.timestamp, value=sample.value)


def normalize_query_time(value: datetime | None, name: str) -> datetime | None:
    if value is None:
        return None
    try:
        return ensure_utc(value)
    except ValueError as exc:
        raise bad_request(f"{name} must include a UTC offset.") from exc


def get_existing_patient_id(db: Session, patient_id: str) -> UUID:
    parsed_patient_id = parse_patient_id(patient_id)
    if crud.get_patient(db, parsed_patient_id) is None:
        raise patient_not_found()
    return parsed_patient_id


@router.post(
    "/temperature",
    operation_id="ingestTemperatureMinute",
    status_code=status.HTTP_201_CREATED,
    response_model=TemperatureIngestionResponse,
    responses={
        400: {"model": Error},
        401: {"model": Error},
        404: {"model": Error},
        409: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params())],
)
async def ingest_temperature_minute(
    patient_id: str,
    temperature_minute: TemperatureMinute,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> TemperatureIngestionResponse:
    parsed_patient_id = get_existing_patient_id(db, patient_id)
    if temperature_minute.timestamp.second != 0 or temperature_minute.timestamp.microsecond != 0:
        raise bad_request("Timestamp must be aligned to a minute boundary.")
    if not crud.add_temperature(db, parsed_patient_id, temperature_minute):
        raise duplicate_metric()
    return TemperatureIngestionResponse(
        patient_id=parsed_patient_id,
        timestamp=temperature_minute.timestamp,
        value=temperature_minute.value,
    )


@router.get(
    "/temperature",
    operation_id="getTemperatureHistory",
    response_model=TemperatureHistoryResponse,
    responses={
        400: {"model": Error},
        401: {"model": Error},
        404: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params("start_time", "end_time", "limit", "offset"))],
)
async def get_temperature_history(
    patient_id: str,
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0, le=100000),
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> TemperatureHistoryResponse:
    parsed_patient_id = get_existing_patient_id(db, patient_id)
    start_time = normalize_query_time(start_time, "start_time")
    end_time = normalize_query_time(end_time, "end_time")
    samples, total = crud.list_temperature(db, parsed_patient_id, start_time, end_time, limit, offset)
    return TemperatureHistoryResponse(
        data=[sample_to_schema(sample) for sample in samples],
        pagination=Pagination(total=total, limit=limit, offset=offset),
    )


@router.post(
    "/heart-rate",
    operation_id="ingestHeartRateBatch",
    status_code=status.HTTP_201_CREATED,
    response_model=HeartRateIngestionResponse,
    responses={
        400: {"model": Error},
        401: {"model": Error},
        404: {"model": Error},
        409: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params())],
)
async def ingest_heart_rate_batch(
    patient_id: str,
    heart_rate_batch: HeartRateBatch,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> HeartRateIngestionResponse:
    parsed_patient_id = get_existing_patient_id(db, patient_id)
    if not crud.add_heart_rate_batch(db, parsed_patient_id, heart_rate_batch):
        raise duplicate_metric()
    return HeartRateIngestionResponse(
        patient_id=parsed_patient_id,
        start_timestamp=heart_rate_batch.start_timestamp,
        samples_stored=len(heart_rate_batch.samples),
    )


@router.get(
    "/heart-rate",
    operation_id="getHeartRateHistory",
    response_model=HeartRateHistoryResponse,
    responses={
        400: {"model": Error},
        401: {"model": Error},
        404: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params("start_time", "end_time", "limit", "offset"))],
)
async def get_heart_rate_history(
    patient_id: str,
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0, le=100000),
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> HeartRateHistoryResponse:
    parsed_patient_id = get_existing_patient_id(db, patient_id)
    start_time = normalize_query_time(start_time, "start_time")
    end_time = normalize_query_time(end_time, "end_time")
    samples, total = crud.list_heart_rate(db, parsed_patient_id, start_time, end_time, limit, offset)
    return HeartRateHistoryResponse(
        data=[sample_to_schema(sample) for sample in samples],
        pagination=Pagination(total=total, limit=limit, offset=offset),
    )
