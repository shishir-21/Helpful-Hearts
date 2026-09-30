from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.auth import router as auth_router
from app.api.routes.doctors import router as doctors_router
from app.api.routes.admin_doctors import router as admin_doctors_router
from app.core.config import settings
from app.db.session import check_database_connection

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Doctor discovery, appointment booking, and health information API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(admin_doctors_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    """Liveness check: confirms that the API process is responding."""
    return {"status": "ok"}


@app.get("/api/v1/health/ready", tags=["Health"])
def readiness() -> dict[str, str]:
    """Readiness check: confirms the API can reach PostgreSQL."""
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready", "database": "connected"}
