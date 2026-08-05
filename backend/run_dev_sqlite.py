import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-not-for-production")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database.session as session_mod

test_engine = create_engine("sqlite:///./dev.db", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
session_mod.engine = test_engine
session_mod.SessionLocal = TestSessionLocal

import app.database as database_pkg
database_pkg.engine = test_engine
database_pkg.SessionLocal = TestSessionLocal

from app.models import (
    role, user, client, client_site, contract, project, travail,
    intervention, intervention_task, attachment, planning, notification,
    approval_history, audit_log,
)  # noqa
from app.database.session import Base
Base.metadata.create_all(test_engine)

from app.database.seed import run as seed_all
seed_all()

import uvicorn
uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="warning")
