"""Supabase client factories for server-side Data API access."""

from functools import lru_cache

from supabase import Client, ClientOptions, create_client

from app.config import settings

_BACKEND_CLIENT_OPTIONS = ClientOptions(
    auto_refresh_token=False,
    persist_session=False,
)


def _normalize_access_token(access_token: str) -> str:
    token = access_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise ValueError("access_token must not be empty.")
    return token


def create_user_scoped_client(access_token: str) -> Client:
    """Return a Supabase client scoped to the authenticated user.

    Uses the anon key with the user's JWT so PostgREST runs as the
    ``authenticated`` role and RLS policies (``auth.uid()``) apply.
    """
    token = _normalize_access_token(access_token)
    options = _BACKEND_CLIENT_OPTIONS.replace(
        headers={"Authorization": f"Bearer {token}"},
    )
    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=options,
    )


@lru_cache
def get_service_role_client() -> Client:
    """Return a cached Supabase client with service-role privileges.

    Bypasses RLS. Use only for privileged backend writes that still attach
    records to the verified ``user_id`` in application code.
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=_BACKEND_CLIENT_OPTIONS,
    )
