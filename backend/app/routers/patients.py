from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import PatientRecord
from app.schemas import (
    Error,
    Pagination,
    Patient,
    PatientCreate,
    PatientListResponse,
    PatientUpdate,
    ValidationErrorResponse,
)
from app.security import require_api_key
from app.validation import reject_unknown_query_params

router = APIRouter(prefix="/v1/patients", tags=["Patients"])


def patient_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "PATIENT_NOT_FOUND", "message": "Patient not found."},
    )


def parse_patient_id(patient_id: str) -> UUID:
    try:
        return UUID(patient_id)
    except ValueError as exc:
        raise patient_not_found() from exc


def patient_to_schema(patient: PatientRecord) -> Patient:
    return Patient(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        weight=patient.weight,
        profile_picture=patient.profile_picture,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


@router.post(
    "",
    operation_id="createPatient",
    status_code=status.HTTP_201_CREATED,
    response_model=Patient,
    response_model_exclude_none=True,
    responses={
        400: {"model": Error},
        401: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params())],
)
async def create_patient(
    patient_create: PatientCreate,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> Patient:
    return patient_to_schema(crud.create_patient(db, patient_create))


@router.get(
    "",
    operation_id="listPatients",
    response_model=PatientListResponse,
    response_model_exclude_none=True,
    responses={401: {"model": Error}, 422: {"model": ValidationErrorResponse}, 500: {"model": Error}},
    dependencies=[Depends(reject_unknown_query_params("limit", "offset"))],
)
async def list_patients(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0, le=100000),
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> PatientListResponse:
    patients, total = crud.list_patients(db, limit=limit, offset=offset)
    return PatientListResponse(
        data=[patient_to_schema(patient) for patient in patients],
        pagination=Pagination(total=total, limit=limit, offset=offset),
    )


@router.get(
    "/{patient_id}",
    operation_id="getPatient",
    response_model=Patient,
    response_model_exclude_none=True,
    responses={
        401: {"model": Error},
        404: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params())],
)
async def get_patient(
    patient_id: str,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> Patient:
    patient = crud.get_patient(db, parse_patient_id(patient_id))
    if patient is None:
        raise patient_not_found()
    return patient_to_schema(patient)


@router.put(
    "/{patient_id}",
    operation_id="updatePatient",
    response_model=Patient,
    response_model_exclude_none=True,
    responses={
        400: {"model": Error},
        401: {"model": Error},
        404: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params())],
)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> Patient:
    patient = crud.update_patient(db, parse_patient_id(patient_id), patient_update)
    if patient is None:
        raise patient_not_found()
    return patient_to_schema(patient)


@router.delete(
    "/{patient_id}",
    operation_id="deletePatient",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": Error},
        404: {"model": Error},
        422: {"model": ValidationErrorResponse},
        500: {"model": Error},
    },
    dependencies=[Depends(reject_unknown_query_params())],
)
async def delete_patient(
    patient_id: str,
    _: None = Depends(require_api_key),
    db: Session = Depends(get_db),
) -> Response:
    if not crud.delete_patient(db, parse_patient_id(patient_id)):
        raise patient_not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
