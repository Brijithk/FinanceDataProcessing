from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.financial_record import EntryType
from app.schemas.financial_record import RecentActivityItem


class CategoryTotal(BaseModel):
    category: str
    entry_type: EntryType
    total: Decimal


class PeriodTrend(BaseModel):
    period_start: date
    income_total: Decimal
    expense_total: Decimal
    net: Decimal


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    category_totals: list[CategoryTotal]
    recent_activity: list[RecentActivityItem]
    monthly_trends: list[PeriodTrend]
