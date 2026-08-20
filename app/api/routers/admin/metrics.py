from fastapi import APIRouter

from app.api.deps import AdminClaimsDep, DbClientDep
from app.repositories import applications as app_repo
from app.repositories import employees as emp_repo
from app.repositories import quotations as quo_repo

router = APIRouter(tags=["admin-metrics"])


@router.get("/metrics")
async def metrics(_: AdminClaimsDep, client: DbClientDep) -> dict:
    no_process_quotes = ["Contactado", "Cotización Presentada"]
    no_process_apps = ["Visto", "Contactado", "Entrevistado"]

    quotations_nuevas = await quo_repo.count_quotations_by_statuses(client, ["Pendiente"])
    quotations_proceso = await quo_repo.count_quotations_by_statuses(client, no_process_quotes)
    applications_nuevas = await app_repo.count_applications_by_statuses(client, ["Postulado"])
    applications_proceso = await app_repo.count_applications_by_statuses(client, no_process_apps)
    employees_activos = await emp_repo.count_active_employees(client)

    return {
        "quotations": {
            "nuevas": quotations_nuevas,
            "en_proceso": quotations_proceso,
        },
        "applications": {
            "nuevas": applications_nuevas,
            "en_proceso": applications_proceso,
        },
        "employees": {
            "activos": employees_activos,
        },
    }