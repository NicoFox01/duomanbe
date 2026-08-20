from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AsyncClient

from app.core.security import decode_token, is_admin
from app.services.supabase import get_supabase_service_client

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_client() -> AsyncClient:
    client = await get_supabase_service_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no configurado",
        )
    return client


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """Valida el Bearer JWT y exige `app_metadata.role == 'admin'`."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = await decode_token(credentials.credentials)
    if not is_admin(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permisos de administrador",
        )
    return claims


DbClientDep = Annotated[AsyncClient, Depends(get_db_client)]
AdminClaimsDep = Annotated[dict, Depends(get_current_admin)]