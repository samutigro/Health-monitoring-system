# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from health_monitoring_api.apis.system_api_base import BaseSystemApi
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
from health_monitoring_api.models.error import Error
from health_monitoring_api.models.health_check import HealthCheck


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/health",
    responses={
        200: {"model": HealthCheck, "description": "The API is running."},
        500: {"model": Error, "description": "Unexpected server error."},
    },
    tags=["System"],
    summary="Check API health",
    response_model_by_alias=True,
)
async def get_health(
) -> HealthCheck:
    """Public endpoint used to verify that the API is running."""
    if not BaseSystemApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSystemApi.subclasses[0]().get_health()
