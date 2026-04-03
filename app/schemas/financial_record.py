from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.financial_record import EntryType


class FinancialRecordBase(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    entry_type: EntryType
    category: str = Field(min_length=1, max_length=128)
    entry_date: date
    notes: str | None = Field(default=None, max_length=4000)


class FinancialRecordCreate(FinancialRecordBase):
    pass


class FinancialRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    entry_type: EntryType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    entry_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FinancialRecordResponse(FinancialRecordBase):
    id: int
    created_by_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RecentActivityItem(BaseModel):
    id: int
    amount: Decimal
    entry_type: EntryType
    category: str
    entry_date: date
    created_at: datetime


class PaginatedFinancialRecords(BaseModel):
    items: list[FinancialRecordResponse]
    total: int
    skip: int
    limit: int
