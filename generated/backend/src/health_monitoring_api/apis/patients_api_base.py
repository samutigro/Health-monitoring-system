# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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

class BasePatientsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BasePatientsApi.subclasses = BasePatientsApi.subclasses + (cls,)
    async def create_patient(
        self,
        patient_create: Annotated[PatientCreate, Field(description="Patient data used to create a new patient.")],
    ) -> Patient:
        """Creates a new patient profile."""
        ...


    async def delete_patient(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
    ) -> None:
        """Deletes a patient and the associated biometric metrics."""
        ...


    async def get_patient(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
    ) -> Patient:
        """Returns a patient profile by identifier."""
        ...


    async def list_patients(
        self,
        limit: Annotated[Optional[Annotated[int, Field(le=1000, strict=True, ge=1)]], Field(description="Maximum number of records returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records skipped before returning results.")],
    ) -> PatientListResponse:
        """Returns a paginated list of patient profiles."""
        ...


    async def update_patient(
        self,
        patient_id: Annotated[StrictStr, Field(description="Unique identifier of the patient.")],
        patient_update: Annotated[PatientUpdate, Field(description="Patient data used to update an existing patient.")],
    ) -> Patient:
        """Replaces the editable fields of an existing patient profile."""
        ...
