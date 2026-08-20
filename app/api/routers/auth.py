import logging

from fastapi import APIRouter, HTTPException, status

from app.core.security import decode_token, is_admin
from app.schemas.auth import LoginRequest, LoginResponse, LoginUser
from app.services.supabase import get_supabase_auth_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    auth_client = await get_supabase_auth_client()
    if auth_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no configurado",
        )

    try:
        result = await auth_client.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:  # noqa: BLE001 - no revelar detalles del proveedor
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        ) from None

    if result.session is None or not result.session.access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo iniciar sesión",
        )

    claims = await decode_token(result.session.access_token)
    if not is_admin(claims):
        logger.warning("Login de usuario no-admin: %s", result.user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permisos de administrador",
        )

    logger.info("Login OK: %s", result.user.email)
    return LoginResponse(
        access_token=result.session.access_token,
        user=LoginUser(id=result.user.id, email=result.user.email),
    )