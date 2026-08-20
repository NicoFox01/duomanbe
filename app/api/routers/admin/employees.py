from fastapi import APIRouter, HTTPException, Response, status
from pydantic import UUID4

from app.api.deps import AdminClaimsDep, DbClientDep
from app.repositories import employees as repo
from app.schemas.employee import EmployeeCreate, EmployeeOut

router = APIRouter(prefix="/employees", tags=["admin-employees"])


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    _: AdminClaimsDep,
    client: DbClientDep,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[EmployeeOut]:
    rows = await repo.list_employees(
        client, search=search, limit=min(limit, 200), offset=offset
    )
    return [EmployeeOut.model_validate(r) for r in rows]


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    _: AdminClaimsDep,
    client: DbClientDep,
) -> EmployeeOut:
    row = await repo.insert_employee(
        client,
        {
            "full_name": payload.full_name,
            "email": payload.email,
            "phone": payload.phone,
            "role": payload.role,
            "specialties": payload.specialties,
        },
    )
    return EmployeeOut.model_validate(row)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: UUID4,
    _: AdminClaimsDep,
    client: DbClientDep,
) -> Response:
    ok = await repo.soft_delete_employee(client, str(employee_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)