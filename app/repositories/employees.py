from supabase import AsyncClient

TABLE = "employees"


async def insert_employee(client: AsyncClient, data: dict) -> dict:
    resp = await client.table(TABLE).insert(data).execute()
    return resp.data[0]


async def list_employees(
    client: AsyncClient,
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
    if search:
        like = f"%{search}%"
        query = query.or_(f"full_name.ilike.{like},role.ilike.{like},phone.ilike.{like}")
    resp = await query.execute()
    return list(resp.data or [])


async def soft_delete_employee(client: AsyncClient, employee_id: str) -> bool:
    resp = (
        await client.table(TABLE)
        .update({"is_active": False})
        .eq("id", employee_id)
        .eq("is_active", True)
        .execute()
    )
    return bool(resp.data)


async def count_active_employees(client: AsyncClient) -> int:
    resp = (
        await client.table(TABLE).select("id", count="exact").eq("is_active", True).execute()
    )
    return resp.count or 0