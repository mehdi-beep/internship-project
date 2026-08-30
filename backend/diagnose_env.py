"""One-off diagnostic: isolates the exact SQL SQLAlchemy sends when
inserting a Role row, to find out why it sends the enum member's NAME
("DISPLAY") instead of its VALUE ("display"). Delete after use.
"""

from app.database import SessionLocal
from app.models.role import Role, RoleName

db = SessionLocal()
try:
    role = Role(name=RoleName.TECHNICIAN)
    db.add(role)
    db.flush()  # sends the INSERT without committing, so we can inspect then roll back
    print("SUCCESS: inserted", role.id, role.name)
    db.rollback()
except Exception as exc:
    print("FAILED:", repr(exc))
    db.rollback()
finally:
    db.close()
