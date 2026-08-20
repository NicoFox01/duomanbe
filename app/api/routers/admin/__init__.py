"""Routers del área administrativa (protegidos, rol admin)."""

from fastapi import APIRouter

from app.api.routers.admin import applications, employees, metrics, quotations

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(metrics.router)
router.include_router(quotations.router)
router.include_router(applications.router)
router.include_router(employees.router)

__all__ = ["router"]