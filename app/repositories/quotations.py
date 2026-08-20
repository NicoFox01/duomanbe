from collections.abc import Sequence

from supabase import AsyncClient

TABLE = "quotations"


async def insert_quotation(client: AsyncClient, data: dict) -> dict:
    resp = await client.table(TABLE).insert(data).execute()
    return resp.data[0]


async def list_quotations(
    client: AsyncClient,
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
            f"full_name.ilike.{like},company.ilike.{like},email.ilike.{like},phone.ilike.{like},location.ilike.{like}"
        )
    resp = await query.execute()
    return list(resp.data or [])


async def update_quotation_status(client: AsyncClient, quotation_id: str, status: str) -> dict | None:
    resp = (
        await client.table(TABLE)
        .update({"status": status})
        .eq("id", quotation_id)
        .eq("is_active", True)
        .execute()
    )
    return resp.data[0] if resp.data else None


async def soft_delete_quotation(client: AsyncClient, quotation_id: str) -> bool:
    resp = (
        await client.table(TABLE)
        .update({"is_active": False})
        .eq("id", quotation_id)
        .eq("is_active", True)
        .execute()
    )
    return bool(resp.data)


async def count_quotations_by_statuses(client: AsyncClient, statuses: Sequence[str]) -> int:
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