"""Shared pytest fixtures.

Every test in this suite runs against a fresh SQLite database (one temp file
per test) seeded with the real `app.database.seed.run()` — the same approach
used throughout manual verification for Phases 5-9 of this project, now made
permanent and repeatable via pytest instead of one-off scratchpad scripts.
SQLite stands in for Postgres (see README "Running the Database" for why): no
Docker is available in the sandbox this suite was built in.

Reloading `app.*` modules per test (rather than only swapping the engine) is
necessary because several modules do `from app.database import SessionLocal`
at import time, binding that name to whatever engine existed at first import —
a fresh engine per test is invisible to code holding an already-bound
reference from an earlier test unless the module is re-imported.
"""

import importlib
import os
import sys
import tempfile

import pytest
from sqlalchemy import create_engine


@pytest.fixture()
def client():
    """A fully-reloaded, freshly-seeded app + TestClient, isolated per test."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    upload_dir = tempfile.mkdtemp()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
    os.environ["UPLOAD_FOLDER"] = upload_dir

    for module_name in list(sys.modules):
        if module_name.startswith("app.") or module_name == "main" or module_name == "config":
            del sys.modules[module_name]

    # session.py's real engine uses a Postgres-only `connect_timeout` connect_arg
    # that SQLite's DBAPI rejects — patch create_engine for the duration of this
    # one import so the module's own top-level `engine = create_engine(...)`
    # line picks up SQLite-safe args without editing production code.
    real_create_engine = create_engine

    def _sqlite_safe_create_engine(url, **kwargs):
        kwargs.pop("connect_args", None)
        return real_create_engine(url, connect_args={"check_same_thread": False})

    import sqlalchemy

    sqlalchemy.create_engine = _sqlite_safe_create_engine
    try:
        session_module = importlib.import_module("app.database.session")
        # Base.metadata only gains a table once its model module has actually
        # been imported and executed — a fresh Base (from the reload above)
        # starts with an empty metadata until every model file below runs.
        for model_module in [
            "app.models.role",
            "app.models.user",
            "app.models.client",
            "app.models.client_site",
            "app.models.contract",
            "app.models.project",
            "app.models.travail",
            "app.models.intervention",
            "app.models.intervention_task",
            "app.models.intervention_technician",
            "app.models.attachment",
            "app.models.planning",
            "app.models.notification",
            "app.models.approval_history",
            "app.models.audit_log",
        ]:
            importlib.import_module(model_module)
    finally:
        sqlalchemy.create_engine = real_create_engine

    session_module.Base.metadata.create_all(session_module.engine)

    seed_module = importlib.import_module("app.database.seed")
    seed_module.run()

    main_module = importlib.import_module("main")

    from fastapi.testclient import TestClient

    with TestClient(main_module.app) as test_client:
        yield test_client

    import shutil

    shutil.rmtree(upload_dir, ignore_errors=True)
    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture()
def auth_headers(client):
    """Returns a helper: auth_headers("tech01") -> {"Authorization": "Bearer ..."}."""

    def _headers(username: str, password: str = "Password123!") -> dict:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        token = response.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
