from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from math import sin
from uuid import UUID

from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import HeartRateSampleRecord, PatientRecord, TemperatureSampleRecord


ARTIFACT_BASE_URL = os.getenv(
    "ARTIFACT_BASE_URL",
    "http://localhost:8000/artifacts/patients",
).rstrip("/")


def _artifact_url(filename: str) -> str:
    return f"{ARTIFACT_BASE_URL}/{filename}"


SEED_PATIENTS = [
    {
        "id": UUID("11111111-1111-4111-8111-111111111111"),
        "name": "Paperino",
        "age": 27,
        "weight": 78.5,
        "profile_picture": _artifact_url("paperino.webp"),
        "temperature_offset": 0.0,
        "heart_rate_base": 72,
    },
    {
        "id": UUID("22222222-2222-4222-8222-222222222222"),
        "name": "Pippo",
        "age": 34,
        "weight": 62.0,
        "profile_picture": _artifact_url("pippo.jpg"),
        "temperature_offset": -0.2,
        "heart_rate_base": 68,
    },
    {
        "id": UUID("33333333-3333-4333-8333-333333333333"),
        "name": "Zio Paperone",
        "age": 62,
        "weight": 84.2,
        "profile_picture": _artifact_url("zio-paperone.webp"),
        "temperature_offset": 0.1,
        "heart_rate_base": 76,
    },
    {
        "id": UUID("44444444-4444-4444-8444-444444444444"),
        "name": "Archimede",
        "age": 34,
        "weight": 58.4,
        "profile_picture": _artifact_url("archimede.jpg"),
        "temperature_offset": -0.1,
        "heart_rate_base": 64,
    },
    {
        "id": UUID("55555555-5555-4555-8555-555555555555"),
        "name": "Paperina",
        "age": 25,
        "weight": 50.3,
        "profile_picture": _artifact_url("paperina.webp"),
        "temperature_offset": 0.2,
        "heart_rate_base": 80,
    },
]

HEART_RATE_CHUNK_SIZE = 5000


def _floor_to_minute(value: datetime) -> datetime:
    return value.replace(second=0, microsecond=0)


def _temperature_value(patient_index: int, minute_index: int, offset: float) -> float:
    slow_wave = sin((minute_index + patient_index * 11) / 18) * 0.25
    small_wave = sin((minute_index + patient_index * 7) / 5) * 0.08
    value = 36.7 + offset + slow_wave + small_wave
    return round(min(42.0, max(34.0, value)), 1)


def _heart_rate_value(patient_index: int, sample_index: int, base: int) -> float:
    breathing_wave = sin((sample_index + patient_index * 120) / 140) * 4.5
    pulse_variation = sin((sample_index + patient_index * 31) / 17) * 1.8
    slow_trend = sin((sample_index + patient_index * 400) / 2400) * 6.0
    value = base + breathing_wave + pulse_variation + slow_trend
    return round(min(220.0, max(30.0, value)), 1)


def _delete_seed_data(db: Session, patient_ids: list[UUID]) -> None:
    db.execute(
        delete(HeartRateSampleRecord).where(HeartRateSampleRecord.patient_id.in_(patient_ids))
    )
    db.execute(
        delete(TemperatureSampleRecord).where(TemperatureSampleRecord.patient_id.in_(patient_ids))
    )
    db.execute(delete(PatientRecord).where(PatientRecord.id.in_(patient_ids)))


def populate_db(
    db: Session | None = None,
    *,
    hours: int = 2,
    reset_existing_seed: bool = True,
) -> dict[str, int]:
    """Populate the database with deterministic demo patients and metrics.

    The generated time series contains one temperature value per minute and
    heart-rate samples at 10 Hz, matching the API contract.
    """

    if hours < 1:
        raise ValueError("hours must be at least 1.")

    init_db()
    owns_session = db is None
    session = db or SessionLocal()
    patient_ids = [patient["id"] for patient in SEED_PATIENTS]
    started_at = _floor_to_minute(datetime.now(timezone.utc) - timedelta(hours=hours))
    created_at = datetime.now(timezone.utc)
    duration_minutes = hours * 60
    heart_rate_sample_count = hours * 60 * 60 * 10

    try:
        if reset_existing_seed:
            _delete_seed_data(session, patient_ids)

        session.execute(
            insert(PatientRecord),
            [
                {
                    "id": patient["id"],
                    "name": patient["name"],
                    "age": patient["age"],
                    "weight": patient["weight"],
                    "profile_picture": patient["profile_picture"],
                    "created_at": created_at,
                    "updated_at": created_at,
                }
                for patient in SEED_PATIENTS
            ],
        )

        session.execute(
            insert(TemperatureSampleRecord),
            [
                {
                    "patient_id": patient["id"],
                    "timestamp": started_at + timedelta(minutes=minute_index),
                    "value": _temperature_value(
                        patient_index,
                        minute_index,
                        float(patient["temperature_offset"]),
                    ),
                }
                for patient_index, patient in enumerate(SEED_PATIENTS)
                for minute_index in range(duration_minutes)
            ],
        )

        for patient_index, patient in enumerate(SEED_PATIENTS):
            rows: list[dict[str, object]] = []
            for sample_index in range(heart_rate_sample_count):
                rows.append(
                    {
                        "patient_id": patient["id"],
                        "timestamp": started_at + timedelta(milliseconds=sample_index * 100),
                        "value": _heart_rate_value(
                            patient_index,
                            sample_index,
                            int(patient["heart_rate_base"]),
                        ),
                    }
                )

                if len(rows) == HEART_RATE_CHUNK_SIZE:
                    session.execute(insert(HeartRateSampleRecord), rows)
                    rows.clear()

            if rows:
                session.execute(insert(HeartRateSampleRecord), rows)

        session.commit()
        return {
            "patients": len(SEED_PATIENTS),
            "temperature_samples": len(SEED_PATIENTS) * duration_minutes,
            "heart_rate_samples": len(SEED_PATIENTS) * heart_rate_sample_count,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    summary = populate_db()
    print(
        "Seed completed: "
        f"{summary['patients']} patients, "
        f"{summary['temperature_samples']} temperature samples, "
        f"{summary['heart_rate_samples']} heart-rate samples."
    )
