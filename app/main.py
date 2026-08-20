import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, applications, auth, cron, health, quotations
from app.core.config import get_settings
from app.services.supabase import close_clients, warmup_clients

settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await warmup_clients()
    yield
    await close_clients()


app = FastAPI(
    title="DUOMAN API",
    description="Backend serverless para DUOMAN - Plataforma de Gestión y Mantenimiento.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(cron.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(quotations.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")