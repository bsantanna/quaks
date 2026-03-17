from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Body
from typing_extensions import Annotated

from app.core.container import Container
from app.interface.api.waitlist.schema import WaitlistRequest, WaitlistResponse
from app.services.waitlist import WaitlistService

router = APIRouter()


@router.post(
    path="",
    status_code=201,
    response_model=WaitlistResponse,
    operation_id="post_waitlist",
    summary="Register for the waiting list",
    description="""
    Submits a registration to the Quaks waiting list. The user will be
    provisioned in Keycloak by a daily ETL process.

    Parameters (JSON body):
    - `email`: Valid email address.
    - `first_name`: First name.
    - `last_name`: Last name.
    - `username`: Username (min 3 chars, lowercase alphanumeric, hyphens, underscores).
    """,
    responses={
        201: {"description": "Successfully registered"},
        409: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            },
        },
    },
)
@inject
async def post_waitlist(
    body: Annotated[WaitlistRequest, Body(...)],
    waitlist_service: Annotated[
        WaitlistService, Depends(Provide[Container.waitlist_service])
    ],
):
    waitlist_service.register(
        email=body.email,
        username=body.username,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    return WaitlistResponse(status="registered")
