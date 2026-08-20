from collections.abc import Sequence

from supabase import AsyncClient

TABLE = "applications"


async def create_bucket_path(client: AsyncClient, bucket: str, path: str) -> str:
    resp = await client.storage.from_(bucket).create_signed_upload_url(path)
    return resp.get("signedUrl", resp.get("url"))


async def get_signed_url(client: AsyncClient, bucket: str, path: str, expires_in: int = 3600) -> str | None:
    if not path:
        return None
    try:
        resp = await client.storage.from_(bucket).create_signed_url(path, expires_in)
    except Exception:  # noqa: BLE001 - archivo ausente: no romper la lista
        return None
    return resp.get("signedUrl", resp.get("url"))


async def insert_application(client: AsyncClient, data: dict) -> dict:
    resp = await client.table(TABLE).insert(data).execute()
    return resp.data[0]


async def list_applications(
    client: AsyncClient,
    bucket: str,
    status: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = (
        client.table(TABLE)
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if status:
        query = query.eq("status", status)
    if search:
        like = f"%{search}%"
        query = query.or_(
            f"full_name.ilike.{like},email.ilike.{like},phone.ilike.{like},target_role.ilike.{like}"
        )
    resp = await query.execute()
    rows = list(resp.data or [])
    for row in rows:
        row["signed_resume_url"] = await get_signed_url(client, bucket, row.get("resume_url", ""))
    return rows


async def update_application_status(client: AsyncClient, application_id: str, status: str) -> dict | None:
    resp = (
        await client.table(TABLE)
        .update({"status": status})
        .eq("id", application_id)
        .eq("is_active", True)
        .execute()
    )
    return resp.data[0] if resp.data else None


async def soft_delete_application(client: AsyncClient, application_id: str) -> bool:
    resp = (
        await client.table(TABLE)
        .update({"is_active": False})
        .eq("id", application_id)
        .eq("is_active", True)
        .execute()
    )
    return bool(resp.data)


async def count_applications_by_statuses(client: AsyncClient, statuses: Sequence[str]) -> int:
    if not statuses:
        return 0
    resp = (
        await client.table(TABLE)
        .select("id", count="exact")
        .eq("is_active", True)
        .in_("status", list(statuses))
        .execute()
    )
    return resp.count or 0