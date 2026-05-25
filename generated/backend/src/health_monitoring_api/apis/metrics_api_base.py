# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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

class BaseMetricsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseMetricsApi.subclasses = BaseMetricsApi.subclasses + (cls,)
    async def get_heart_rate_history(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
        start_time: Annotated[Optional[datetime], Field(description="Inclusive start of the time range, expressed as UTC ISO 8601 date-time.")],
        end_time: Annotated[Optional[datetime], Field(description="Exclusive end of the time range, expressed as UTC ISO 8601 date-time.")],
        limit: Annotated[Optional[Annotated[int, Field(le=1000, strict=True, ge=1)]], Field(description="Maximum number of records returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records skipped before returning results.")],
    ) -> HeartRateHistoryResponse:
        """Returns raw heart rate samples for one patient in the requested time range."""
        ...


    async def get_temperature_history(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
        start_time: Annotated[Optional[datetime], Field(description="Inclusive start of the time range, expressed as UTC ISO 8601 date-time.")],
        end_time: Annotated[Optional[datetime], Field(description="Exclusive end of the time range, expressed as UTC ISO 8601 date-time.")],
        limit: Annotated[Optional[Annotated[int, Field(le=1000, strict=True, ge=1)]], Field(description="Maximum number of records returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records skipped before returning results.")],
    ) -> TemperatureHistoryResponse:
        """Returns one temperature value per minute for one patient."""
        ...


    async def ingest_heart_rate_batch(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
        heart_rate_batch: Annotated[HeartRateBatch, Field(description="Heart rate batch sampled at 10 Hz for exactly 60 seconds.")],
    ) -> HeartRateIngestionResponse:
        """Stores a heart rate batch for one patient.  The batch represents exactly 60 seconds of heart rate data sampled at 10 Hz, therefore the request must contain exactly 600 values.  Individual sample timestamps are derived by the backend using:  &#x60;sample_timestamp &#x3D; start_timestamp + index / 10 seconds&#x60; """
        ...


    async def ingest_temperature_minute(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
        temperature_minute: Annotated[TemperatureMinute, Field(description="One temperature average value for a single minute.")],
    ) -> TemperatureIngestionResponse:
        """Stores one aggregated body temperature value for one patient.  The timestamp must be aligned to a minute boundary. In practice this means seconds and sub-seconds should be zero. """
        ...
