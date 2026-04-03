from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.database import get_db
from app.models.financial_record import EntryType, FinancialRecord
from app.models.user import Role, User
from app.schemas.financial_record import (
    FinancialRecordCreate,
    FinancialRecordResponse,
    FinancialRecordUpdate,
    PaginatedFinancialRecords,
)

router = APIRouter(prefix="/records", tags=["records"])


def _records_select(
    *,
    from_date: date | None,
    to_date: date | None,
    category: str | None,
    entry_type: EntryType | None,
):
    q = select(FinancialRecord).where(FinancialRecord.deleted_at.is_(None))
    if from_date is not None:
        q = q.where(FinancialRecord.entry_date >= from_date)
    if to_date is not None:
        q = q.where(FinancialRecord.entry_date <= to_date)
    if category is not None:
        q = q.where(FinancialRecord.category == category)
    if entry_type is not None:
        q = q.where(FinancialRecord.entry_type == entry_type)
    return q


@router.get("", response_model=PaginatedFinancialRecords)
async def list_records(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(Role.analyst, Role.admin))],
    from_date: Annotated[date | None, Query(description="Inclusive lower bound for entry_date")] = None,
    to_date: Annotated[date | None, Query(description="Inclusive upper bound for entry_date")] = None,
    category: str | None = None,
    entry_type: EntryType | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaginatedFinancialRecords:
    base = _records_select(
        from_date=from_date,
        to_date=to_date,
        category=category,
        entry_type=entry_type,
    )
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows = await db.execute(
        base.order_by(FinancialRecord.entry_date.desc(), FinancialRecord.id.desc()).offset(skip).limit(limit)
    )
    items = list(rows.scalars().all())
    return PaginatedFinancialRecords(items=items, total=int(total), skip=skip, limit=limit)


@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    body: FinancialRecordCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(Role.admin))],
) -> FinancialRecord:
    rec = FinancialRecord(
        amount=body.amount,
        entry_type=body.entry_type,
        category=body.category.strip(),
        entry_date=body.entry_date,
        notes=body.notes,
        created_by_id=user.id,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


@router.get("/{record_id}", response_model=FinancialRecordResponse)
async def get_record(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(Role.analyst, Role.admin))],
) -> FinancialRecord:
    result = await db.execute(
        select(FinancialRecord).where(FinancialRecord.id == record_id, FinancialRecord.deleted_at.is_(None))
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return rec


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
async def update_record(
    record_id: int,
    body: FinancialRecordUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(Role.admin))],
) -> FinancialRecord:
    result = await db.execute(
        select(FinancialRecord).where(FinancialRecord.id == record_id, FinancialRecord.deleted_at.is_(None))
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if body.amount is not None:
        rec.amount = body.amount
    if body.entry_type is not None:
        rec.entry_type = body.entry_type
    if body.category is not None:
        rec.category = body.category.strip()
    if body.entry_date is not None:
        rec.entry_date = body.entry_date
    if body.notes is not None:
        rec.notes = body.notes
    await db.commit()
    await db.refresh(rec)
    return rec


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(Role.admin))],
) -> None:
    result = await db.execute(
        select(FinancialRecord).where(FinancialRecord.id == record_id, FinancialRecord.deleted_at.is_(None))
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    rec.deleted_at = datetime.now(timezone.utc)
    await db.commit()
