from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AuthApiError, AuthError, Client

from app.database.supabase import create_user_scoped_client

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: str
    email: str
    access_token: str


def _unauthorized(detail: str = "Invalid or expired credentials.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Missing bearer token.")

    token = credentials.credentials.strip()
    if not token:
        raise _unauthorized("Missing bearer token.")

    return token


def get_current_user(
    access_token: Annotated[str, Depends(get_bearer_token)],
) -> CurrentUser:
    client = create_user_scoped_client(access_token)

    try:
        response = client.auth.get_user(jwt=access_token)
    except (AuthApiError, AuthError):
        raise _unauthorized() from None

    if response is None or response.user is None:
        raise _unauthorized()

    user = response.user
    if not user.email:
        raise _unauthorized("Authenticated user has no email.")

    return CurrentUser(
        id=str(user.id),
        email=user.email,
        access_token=access_token,
    )


def get_user_scoped_supabase(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Client:
    return create_user_scoped_client(current_user.access_token)
