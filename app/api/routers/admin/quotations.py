from fastapi import APIRouter, HTTPException, Response, status
from pydantic import UUID4

from app.api.deps import AdminClaimsDep, DbClientDep
from app.repositories import quotations as repo
from app.schemas.enums import QuotationStatus
from app.schemas.quotation import QuotationOut, QuotationStatusUpdate

router = APIRouter(prefix="/quotations", tags=["admin-quotations"])


@router.get("", response_model=list[QuotationOut])
async def list_quotations(
    _: AdminClaimsDep,
    client: DbClientDep,
    status_filter: QuotationStatus | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[QuotationOut]:
    rows = await repo.list_quotations(
        client,
        status=status_filter.value if status_filter else None,
        search=search,
        limit=min(limit, 200),
        offset=offset,
    )
    return [QuotationOut.model_validate(r) for r in rows]


@router.patch("/{quotation_id}/status", response_model=QuotationOut)
async def update_status(
    quotation_id: UUID4,
    payload: QuotationStatusUpdate,
    _: AdminClaimsDep,
    client: DbClientDep,
) -> QuotationOut:
    row = await repo.update_quotation_status(client, str(quotation_id), payload.status.value)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    return QuotationOut.model_validate(row)


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quotation(
    quotation_id: UUID4,
    _: AdminClaimsDep,
    client: DbClientDep,
) -> Response:
    ok = await repo.soft_delete_quotation(client, str(quotation_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)