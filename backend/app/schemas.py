from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a UTC offset.")
    return value.astimezone(timezone.utc)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthCheck(ContractModel):
    status: str = Field(pattern="^ok$")
    service: str
    version: str


class PatientCreate(ContractModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    age: Annotated[int, Field(ge=0, le=120)]
    weight: Annotated[float, Field(gt=0, le=400)]
    profile_picture: Annotated[AnyUrl, Field(max_length=2048)] | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_contain_null_byte(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("name must not contain null bytes.")
        return value

    @field_validator("age", mode="before")
    @classmethod
    def age_must_be_integer(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("age must be an integer.")
        return value

    @field_validator("weight", mode="before")
    @classmethod
    def weight_must_be_number(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("weight must be a number.")
        return value

    @field_validator("profile_picture", mode="before")
    @classmethod
    def profile_picture_must_not_be_null_when_present(cls, value: object) -> object:
        if value is None:
            raise ValueError("profile_picture must be omitted or contain a URL.")
        return value

    @field_validator("profile_picture")
    @classmethod
    def profile_picture_must_be_http_url(cls, value: AnyUrl | None) -> AnyUrl | None:
        if value is not None and value.scheme not in {"http", "https"}:
            raise ValueError("profile_picture must use http or https.")
        return value


class PatientUpdate(PatientCreate):
    pass


class Patient(ContractModel):
    id: UUID
    name: Annotated[str, Field(min_length=1, max_length=120)]
    age: Annotated[int, Field(ge=0, le=120)]
    weight: Annotated[float, Field(gt=0, le=400)]
    profile_picture: Annotated[AnyUrl, Field(max_length=2048)] | None = None
    created_at: datetime
    updated_at: datetime


class Pagination(ContractModel):
    total: Annotated[int, Field(ge=0)]
    limit: Annotated[int, Field(ge=1, le=1000)]
    offset: Annotated[int, Field(ge=0)]


class PatientListResponse(ContractModel):
    data: list[Patient]
    pagination: Pagination


class MetricSample(ContractModel):
    timestamp: datetime
    value: float


class HeartRateHistoryResponse(ContractModel):
    data: list[MetricSample]
    pagination: Pagination


class TemperatureHistoryResponse(ContractModel):
    data: list[MetricSample]
    pagination: Pagination


class HeartRateBatch(ContractModel):
    start_timestamp: datetime
    samples: Annotated[
        list[Annotated[float, Field(ge=30, le=220)]],
        Field(min_length=600, max_length=600),
    ]

    @field_validator("start_timestamp", mode="before")
    @classmethod
    def start_timestamp_must_be_string(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("start_timestamp must be an ISO 8601 string.")
        return value

    @field_validator("start_timestamp")
    @classmethod
    def start_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("samples", mode="before")
    @classmethod
    def samples_must_not_contain_booleans(cls, value: object) -> object:
        if isinstance(value, list) and any(
            isinstance(item, bool) or not isinstance(item, int | float) for item in value
        ):
            raise ValueError("Heart rate samples must be numbers.")
        return value


class TemperatureMinute(ContractModel):
    timestamp: datetime
    value: Annotated[float, Field(ge=34, le=42)]

    @field_validator("timestamp", mode="before")
    @classmethod
    def timestamp_must_be_string(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("timestamp must be an ISO 8601 string.")
        return value

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("value", mode="before")
    @classmethod
    def value_must_not_be_boolean(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("Temperature value must be a number.")
        return value


class HeartRateIngestionResponse(ContractModel):
    patient_id: UUID
    start_timestamp: datetime
    samples_stored: Annotated[int, Field(ge=600, le=600)]


class TemperatureIngestionResponse(ContractModel):
    patient_id: UUID
    timestamp: datetime
    value: Annotated[float, Field(ge=34, le=42)]


class Error(ContractModel):
    code: str
    message: str


class ErrorDetail(ContractModel):
    field: str
    issue: str


class ValidationErrorResponse(ContractModel):
    code: str
    message: str
    details: list[ErrorDetail]
