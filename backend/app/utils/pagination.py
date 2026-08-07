from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.pagination import Page


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> Page:
    total = db.scalar(select_count(stmt)) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    pages = (total + page_size - 1) // page_size if total else 0
    return Page(items=list(items), total=total, page=page, page_size=page_size, pages=pages)


def select_count(stmt: Select) -> Select:
    # with_only_columns(func.count()) used to strip the entire FROM/WHERE clause,
    # not just the selected columns — the compiled query was literally
    # "SELECT count(*)" with no table reference, which every SQL dialect resolves
    # to a constant 1 rather than the real row count. Wrapping the original
    # (filtered) statement as a subquery and counting from it is the standard,
    # correct pattern — it preserves every WHERE/JOIN already applied.
    return select(func.count()).select_from(stmt.order_by(None).subquery())
