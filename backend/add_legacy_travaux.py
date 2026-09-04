"""One-off insertion of LEGACY_PLACEHOLDER_TRAVAUX_CATALOG's 125 rows into an
already-seeded production database (which already has the 58 real travaux
from TRAVAUX_CATALOG). Not part of seed_travaux()'s normal path since that
only ever runs on a from-scratch database -- this targets an existing one
without touching anything already there. Safe to re-run: skips any code
already present. Delete after use.
"""

from app.database import SessionLocal
from app.database.seed import LEGACY_PLACEHOLDER_TRAVAUX_CATALOG
from app.models.travail import Travail

db = SessionLocal()
try:
    existing_codes = {row[0] for row in db.query(Travail.travail_code).all()}
    to_insert = [
        Travail(travail_code=code, travail_name=name, category=category, active=True)
        for code, name, category in LEGACY_PLACEHOLDER_TRAVAUX_CATALOG
        if code not in existing_codes
    ]
    print(f"existing travaux: {len(existing_codes)}")
    print(f"legacy catalog size: {len(LEGACY_PLACEHOLDER_TRAVAUX_CATALOG)}")
    print(f"inserting: {len(to_insert)}")
    db.add_all(to_insert)
    db.commit()
    print(f"total travaux now: {db.query(Travail).count()}")
except Exception:
    db.rollback()
    raise
finally:
    db.close()
