from datetime import datetime, timedelta, timezone
from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import HeartRateSampleRecord, PatientRecord, TemperatureSampleRecord
from app.schemas import HeartRateBatch, PatientCreate, PatientUpdate, TemperatureMinute

SampleRecord = TypeVar("SampleRecord", TemperatureSampleRecord, HeartRateSampleRecord)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_patient(db: Session, payload: PatientCreate) -> PatientRecord:
    timestamp = now_utc()
    patient = PatientRecord(
        id=uuid4(),
        name=payload.name,
        age=payload.age,
        weight=payload.weight,
        profile_picture=str(payload.profile_picture) if payload.profile_picture else None,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def list_patients(db: Session, limit: int, offset: int) -> tuple[list[PatientRecord], int]:
    total = db.scalar(select(func.count()).select_from(PatientRecord)) or 0
    if offset >= total:
        return [], total
    patients = db.scalars(
        select(PatientRecord)
        .order_by(PatientRecord.created_at.desc(), PatientRecord.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(patients), total


def get_patient(db: Session, patient_id: UUID) -> PatientRecord | None:
    return db.get(PatientRecord, patient_id)


def update_patient(db: Session, patient_id: UUID, payload: PatientUpdate) -> PatientRecord | None:
    patient = get_patient(db, patient_id)
    if patient is None:
        return None

    patient.name = payload.name
    patient.age = payload.age
    patient.weight = payload.weight
    patient.profile_picture = str(payload.profile_picture) if payload.profile_picture else None
    patient.updated_at = now_utc()
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: UUID) -> bool:
    patient = get_patient(db, patient_id)
    if patient is None:
        return False

    db.delete(patient)
    db.commit()
    return True


def add_temperature(db: Session, patient_id: UUID, payload: TemperatureMinute) -> bool:
    sample = TemperatureSampleRecord(
        patient_id=patient_id,
        timestamp=payload.timestamp,
        value=payload.value,
    )
    db.add(sample)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False
    return True


def add_heart_rate_batch(db: Session, patient_id: UUID, payload: HeartRateBatch) -> bool:
    samples = [
        HeartRateSampleRecord(
            patient_id=patient_id,
            timestamp=payload.start_timestamp + timedelta(milliseconds=index * 100),
            value=value,
        )
        for index, value in enumerate(payload.samples)
    ]
    timestamps = [sample.timestamp for sample in samples]
    existing_timestamp = db.scalar(
        select(HeartRateSampleRecord.timestamp)
        .where(
            HeartRateSampleRecord.patient_id == patient_id,
            HeartRateSampleRecord.timestamp.in_(timestamps),
        )
        .limit(1)
    )
    if existing_timestamp is not None:
        return False

    db.add_all(samples)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return False
    return True


def list_temperature(
    db: Session,
    patient_id: UUID,
    start_time: datetime | None,
    end_time: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[TemperatureSampleRecord], int]:
    return _list_samples(db, TemperatureSampleRecord, patient_id, start_time, end_time, limit, offset)


def list_heart_rate(
    db: Session,
    patient_id: UUID,
    start_time: datetime | None,
    end_time: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[HeartRateSampleRecord], int]:
    return _list_samples(db, HeartRateSampleRecord, patient_id, start_time, end_time, limit, offset)


def _list_samples(
    db: Session,
    model: type[SampleRecord],
    patient_id: UUID,
    start_time: datetime | None,
    end_time: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[SampleRecord], int]:
    filters = [model.patient_id == patient_id]
    if start_time is not None:
        filters.append(model.timestamp >= start_time)
    if end_time is not None:
        filters.append(model.timestamp < end_time)

    total = db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    if offset >= total:
        return [], total
    samples = db.scalars(
        select(model)
        .where(*filters)
        .order_by(model.timestamp)
        .offset(offset)
        .limit(limit)
    ).all()
    return list(samples), total
