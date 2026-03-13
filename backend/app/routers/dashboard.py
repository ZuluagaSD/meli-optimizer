from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.listing import Listing
from app.models.meli_account import MeliAccount
from app.models.optimization import Optimization
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    total_listings: int
    active_listings: int
    paused_listings: int
    avg_completeness: float
    health_distribution: dict[str, int]
    site_distribution: dict[str, int]
    total_optimizations: int
    applied_optimizations: int
    listings_needing_attention: int  # completeness < 70%


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_ids_stmt = select(MeliAccount.id).where(
        MeliAccount.tenant_id == user.tenant_id, MeliAccount.is_active == True
    )
    base = select(Listing).where(Listing.meli_account_id.in_(account_ids_stmt))

    # Total and active counts
    total_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count()).select_from(
            base.where(Listing.status == "active").subquery()
        )
    )
    active = active_result.scalar() or 0

    paused_result = await db.execute(
        select(func.count()).select_from(
            base.where(Listing.status == "paused").subquery()
        )
    )
    paused = paused_result.scalar() or 0

    # Average completeness
    avg_result = await db.execute(
        select(func.avg(Listing.attribute_completeness_pct)).where(
            Listing.meli_account_id.in_(account_ids_stmt)
        )
    )
    avg_completeness = round(avg_result.scalar() or 0, 1)

    # Health distribution
    health_result = await db.execute(
        select(Listing.health_status, func.count())
        .where(Listing.meli_account_id.in_(account_ids_stmt))
        .group_by(Listing.health_status)
    )
    health_dist = {row[0] or "unknown": row[1] for row in health_result.all()}

    # Site distribution
    site_result = await db.execute(
        select(Listing.site_id, func.count())
        .where(Listing.meli_account_id.in_(account_ids_stmt))
        .group_by(Listing.site_id)
    )
    site_dist = {row[0]: row[1] for row in site_result.all()}

    # Optimization stats
    listing_ids_stmt = select(Listing.id).where(
        Listing.meli_account_id.in_(account_ids_stmt)
    )
    opt_total_result = await db.execute(
        select(func.count()).where(Optimization.listing_id.in_(listing_ids_stmt))
    )
    total_opts = opt_total_result.scalar() or 0

    opt_applied_result = await db.execute(
        select(func.count()).where(
            Optimization.listing_id.in_(listing_ids_stmt),
            Optimization.status == "applied",
        )
    )
    applied_opts = opt_applied_result.scalar() or 0

    # Listings needing attention (completeness < 70%)
    attention_result = await db.execute(
        select(func.count()).select_from(
            base.where(Listing.attribute_completeness_pct < 70).subquery()
        )
    )
    needing_attention = attention_result.scalar() or 0

    return DashboardStats(
        total_listings=total,
        active_listings=active,
        paused_listings=paused,
        avg_completeness=avg_completeness,
        health_distribution=health_dist,
        site_distribution=site_dist,
        total_optimizations=total_opts,
        applied_optimizations=applied_opts,
        listings_needing_attention=needing_attention,
    )
