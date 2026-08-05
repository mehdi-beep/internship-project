from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.intervention import Intervention

BI_PREFIX = "BI"
BI_DIGITS = 6


def format_bi_number(sequence: int) -> str:
    """Rule 6 (Ch.10/Ch.21): BI000001, BI000002, ... — never typed manually."""
    return f"{BI_PREFIX}{sequence:0{BI_DIGITS}d}"


def next_bi_number(db: Session) -> str:
    """Reads the highest existing bi_number and returns the next one in sequence.

    Not safe against concurrent inserts on its own — callers must hold this within
    the same transaction that inserts the intervention row (and the interventions.bi_number
    UNIQUE constraint is the final safety net against a race).
    """
    highest = db.scalar(select(func.max(Intervention.bi_number)))
    if highest is None:
        return format_bi_number(1)
    return format_bi_number(int(highest.removeprefix(BI_PREFIX)) + 1)
