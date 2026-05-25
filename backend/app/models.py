from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Identity, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PatientRecord(Base):
    __tablename__ = "patients"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    profile_picture: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    temperature_samples: Mapped[list["TemperatureSampleRecord"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    heart_rate_samples: Mapped[list["HeartRateSampleRecord"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TemperatureSampleRecord(Base):
    __tablename__ = "temperature_samples"
    __table_args__ = (
        UniqueConstraint("patient_id", "timestamp", name="uq_temperature_patient_timestamp"),
        Index("ix_temperature_patient_timestamp", "patient_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    patient: Mapped[PatientRecord] = relationship(back_populates="temperature_samples")


class HeartRateSampleRecord(Base):
    __tablename__ = "heart_rate_samples"
    __table_args__ = (
        UniqueConstraint("patient_id", "timestamp", name="uq_heart_rate_patient_timestamp"),
        Index("ix_heart_rate_patient_timestamp", "patient_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    patient: Mapped[PatientRecord] = relationship(back_populates="heart_rate_samples")
