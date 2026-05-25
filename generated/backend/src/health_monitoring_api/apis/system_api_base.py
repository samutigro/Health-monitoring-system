# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from health_monitoring_api.models.error import Error
from health_monitoring_api.models.health_check import HealthCheck


class BaseSystemApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSystemApi.subclasses = BaseSystemApi.subclasses + (cls,)
    async def get_health(
        self,
    ) -> HealthCheck:
        """Public endpoint used to verify that the API is running."""
        ...
