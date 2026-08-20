import asyncio
import logging

from supabase import AsyncClient, create_async_client

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_service_client: AsyncClient | None = None
_public_client: AsyncClient | None = None
_auth_client: AsyncClient | None = None
_lock = asyncio.Lock()


async def get_supabase_service_client() -> AsyncClient | None:
    """Cliente async con la Service Role Key (bypass de RLS). Solo backend."""
    global _service_client
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    if _service_client is None:
        async with _lock:
            if _service_client is None:
                _service_client = await create_async_client(
                    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
                )
    return _service_client


async def get_supabase_public_client() -> AsyncClient | None:
    """Cliente async con la Anon/Public Key (respeta RLS)."""
    global _public_client
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None
    if _public_client is None:
        async with _lock:
            if _public_client is None:
                _public_client = await create_async_client(
                    settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
                )
    return _public_client


async def get_supabase_auth_client() -> AsyncClient | None:
    """Cliente async DEDICADO al login (sign_in_with_password).

    OJO: sign_in_with_password muta el contexto auth del cliente. Por eso
    se usa una instancia aparte, nunca la de tablas/storage (rompería RLS
    al enviar el token del usuario en lugar de la service role key).
    """
    global _auth_client
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        return None
    if _auth_client is None:
        async with _lock:
            if _auth_client is None:
                _auth_client = await create_async_client(
                    settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY
                )
    return _auth_client


async def warmup_clients() -> None:
    """Pre-calienta los clientes al arrancar la app."""
    try:
        await get_supabase_service_client()
        logger.info("Cliente Supabase inicializado (service role)")
    except Exception as exc:  # noqa: BLE001 - arranque no debe romper la app
        logger.warning("Supabase no disponible al arrancar: %s", exc)


async def close_clients() -> None:
    """Cierre best-effort. En serverless el proceso se destruye igualmente."""
    global _service_client, _public_client
    for client in (_service_client, _public_client):
        closer = getattr(client, "aclose", None)
        if closer is not None:
            try:
                await closer()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Error cerrando cliente Supabase: %s", exc)
    _service_client = None
    _public_client = None