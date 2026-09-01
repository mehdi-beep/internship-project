"""One-off diagnostic: calls the exact same auth_service.authenticate()
function the /api/auth/login endpoint uses, to catch anything a direct
password-hash check might miss (active flag, role lookup, DB session
behavior). Delete after use.
"""

from app.database import SessionLocal
from app.services import auth_service
from app.services.auth_service import InvalidCredentialsError

db = SessionLocal()
try:
    user, token = auth_service.authenticate(db, "tech01", "Password123!")
    print("SUCCESS")
    print("user id:", user.id)
    print("role:", user.role.name.value)
    print("token (first 40 chars):", token[:40])
except InvalidCredentialsError:
    print("FAILED: InvalidCredentialsError raised")
except Exception as exc:
    print("FAILED with unexpected exception:", repr(exc))
finally:
    db.close()
