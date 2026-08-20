"""Seguridad: verificación de JWT emitidos por Supabase Auth.

Supabase firma los access tokens con claves asimétricas (ES256) publicadas
en su endpoint JWKS, salvo proyectos legacy que usan HS256 con un secreto.
Soportamos ambos.
"""

import logging
import time

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwk, jwt

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_JWKS_CACHE: list[dict] = []
_JWKS_FETCHED_AT = 0.0
_JWKS_TTL_SECONDS = 3600


def _jwks_url(settings) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"


async def _fetch_jwks(settings) -> list[dict]:
    global _JWKS_CACHE, _JWKS_FETCHED_AT
    now = time.monotonic()
    if _JWKS_CACHE and (now - _JWKS_FETCHED_AT) < _JWKS_TTL_SECONDS:
        return _JWKS_CACHE
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_jwks_url(settings))
        resp.raise_for_status()
    _JWKS_CACHE = resp.json().get("keys", [])
    _JWKS_FETCHED_AT = time.monotonic()
    return _JWKS_CACHE


async def decode_token(token: str) -> dict:
    """Valida un JWT de Supabase Auth y devuelve sus claims.

    Lanza 401 si el token es inválido, está mal firmado o expiró.
    """
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "HS256":
            key: object = settings.SUPABASE_JWT_SECRET
        else:
            keys = await _fetch_jwks(settings)
            kid = header.get("kid")
            key_data = next((k for k in keys if k.get("kid") == kid), None)
            if key_data is None:
                raise JWTError("No se encontró la clave pública (kid)")
            key = jwk.construct(key_data, algorithm=alg)

        claims = jwt.decode(token, key, algorithms=[alg], audience="authenticated")
    except (JWTError, httpx.HTTPError, KeyError, ValueError):
        logger.info("Token JWT rechazado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return claims


def is_admin(claims: dict) -> bool:
    app_metadata = claims.get("app_metadata") or {}
    return app_metadata.get("role") == "admin"