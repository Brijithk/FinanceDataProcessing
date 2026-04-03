from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_record import EntryType, FinancialRecord
from app.schemas.dashboard import CategoryTotal, DashboardSummary, PeriodTrend
from app.schemas.financial_record import RecentActivityItem


def _month_start(ym: str) -> date:
    y, m = ym.split("-", 1)
    return date(int(y), int(m), 1)


async def build_dashboard_summary(
    db: AsyncSession,
    *,
    recent_limit: int = 10,
    trend_months: int = 12,
) -> DashboardSummary:
    active = FinancialRecord.deleted_at.is_(None)

    total_income = await db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            active,
            FinancialRecord.entry_type == EntryType.income,
        )
    )
    total_expenses = await db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            active,
            FinancialRecord.entry_type == EntryType.expense,
        )
    )
    ti = Decimal(str(total_income or 0))
    te = Decimal(str(total_expenses or 0))

    cat_rows = await db.execute(
        select(
            FinancialRecord.category,
            FinancialRecord.entry_type,
            func.sum(FinancialRecord.amount),
        )
        .where(active)
        .group_by(FinancialRecord.category, FinancialRecord.entry_type)
        .order_by(FinancialRecord.category)
    )
    category_totals = [
        CategoryTotal(category=r[0], entry_type=r[1], total=Decimal(str(r[2]))) for r in cat_rows.all()
    ]

    recent_rows = await db.execute(
        select(FinancialRecord)
        .where(active)
        .order_by(FinancialRecord.entry_date.desc(), FinancialRecord.id.desc())
        .limit(recent_limit)
    )
    recent_activity = [
        RecentActivityItem(
            id=r.id,
            amount=r.amount,
            entry_type=r.entry_type,
            category=r.category,
            entry_date=r.entry_date,
            created_at=r.created_at,
        )
        for r in recent_rows.scalars().all()
    ]

    ym = func.strftime("%Y-%m", FinancialRecord.entry_date).label("ym")
    inc = func.sum(
        case((FinancialRecord.entry_type == EntryType.income, FinancialRecord.amount), else_=0)
    )
    exp = func.sum(
        case((FinancialRecord.entry_type == EntryType.expense, FinancialRecord.amount), else_=0)
    )
    trend_rows = await db.execute(
        select(ym, inc, exp)
        .where(active)
        .group_by(ym)
        .order_by(ym.desc())
        .limit(trend_months)
    )
    monthly_trends: list[PeriodTrend] = []
    for row in reversed(trend_rows.all()):
        ym_s, inc_v, exp_v = row[0], row[1], row[2]
        i = Decimal(str(inc_v or 0))
        e = Decimal(str(exp_v or 0))
        monthly_trends.append(
            PeriodTrend(
                period_start=_month_start(ym_s),
                income_total=i,
                expense_total=e,
                net=i - e,
            )
        )

    return DashboardSummary(
        total_income=ti,
        total_expenses=te,
        net_balance=ti - te,
        category_totals=category_totals,
        recent_activity=recent_activity,
        monthly_trends=monthly_trends,
    )
