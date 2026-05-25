from collections.abc import Callable

from fastapi import HTTPException, Request, status


def reject_unknown_query_params(*allowed_params: str) -> Callable[[Request], None]:
    allowed = set(allowed_params)

    def dependency(request: Request) -> None:
        unknown_params = sorted(set(request.query_params.keys()) - allowed)
        if not unknown_params:
            return

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Request query does not match the contract.",
                "details": [
                    {
                        "field": f"query.{param}",
                        "issue": "Unexpected query parameter.",
                    }
                    for param in unknown_params
                ],
            },
        )

    return dependency
