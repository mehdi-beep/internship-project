from sqlalchemy import Select, func
from sqlalchemy.orm import Session

from app.schemas.pagination import Page


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> Page:
    total = db.scalar(select_count(stmt)) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    pages = (total + page_size - 1) // page_size if total else 0
    return Page(items=list(items), total=total, page=page, page_size=page_size, pages=pages)


def select_count(stmt: Select) -> Select:
    return stmt.with_only_columns(func.count()).order_by(None)
