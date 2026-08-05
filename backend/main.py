import logging

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
    travaux,
    users,
)
from config import get_settings

logger = logging.getLogger("bims")

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
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
app.include_router(reports.router, prefix="/api")
