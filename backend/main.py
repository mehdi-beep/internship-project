import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import (
    approvals,
    attachments,
    auth,
    clients,
    contracts,
    dashboard,
    health,
    interventions,
    notifications,
    planning,
    projects,
    reports,
    sites,
    technician_performance,
    travaux,
    users,
)
from config import get_settings

logger = logging.getLogger("bims")

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Safety net for a genuinely empty database (e.g. a fresh Volume or a new
    # Postgres instance with DATABASE_URL pointed at it): both calls below are
    # no-ops against a database that's already set up, so this is safe to run
    # unconditionally on every boot. Deployments that ship a pre-seeded file
    # (e.g. Railway's committed dev.db) are entirely unaffected — nothing here
    # re-seeds or resets existing data.
    import app.models  # noqa: F401  registers every table on Base.metadata
    from app.database import Base, engine
    from app.database.seed import run as seed_all

    Base.metadata.create_all(engine)
    seed_all()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Auth is Bearer-token-only (no cookies, no withCredentials anywhere in the
    # frontend) — allow_credentials=False lets CORS_ORIGINS=* work as a valid,
    # browser-safe default for any deployed frontend origin (e.g. Vercel),
    # since browsers reject a wildcard origin whenever credentials are allowed.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("Database error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"success": False, "message": "Server unavailable. Please try again later."},
    )


app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(sites.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(travaux.router, prefix="/api")
app.include_router(planning.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(interventions.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(technician_performance.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
