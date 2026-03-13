from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.listing import Listing
from app.models.meli_account import MeliAccount
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.listing_sync import sync_listings_for_account
from app.services.meli_client import MeliClient

router = APIRouter(prefix="/listings", tags=["listings"])


# ----- Schemas -----

class ListingResponse(BaseModel):
    id: str
    meli_item_id: str
    site_id: str
    title: str
    category_id: str
    category_name: str
    price: float
    currency_id: str
    status: str
    health_status: str | None
    attribute_completeness_pct: float
    quality_score: int | None
    last_synced_at: str | None

    model_config = {"from_attributes": True}


class ListingDetailResponse(ListingResponse):
    description: str | None
    attributes: list | None
    pictures: list | None
    tags: list | None


class PaginatedListings(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    page_size: int


class SyncResponse(BaseModel):
    status: str
    message: str


class CompetitorResponse(BaseModel):
    title: str
    price: float
    currency_id: str
    permalink: str


# ----- Helpers -----

async def _get_account(db: AsyncSession, account_id: str, tenant_id: str) -> MeliAccount:
    stmt = select(MeliAccount).where(
        MeliAccount.id == account_id,
        MeliAccount.tenant_id == tenant_id,
        MeliAccount.is_active == True,
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="MeLi account not found")
    return account


# ----- Routes -----

@router.post("/sync/{account_id}", response_model=SyncResponse)
async def trigger_sync(
    account_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(db, account_id, user.tenant_id)
    result = await sync_listings_for_account(db, account)
    return SyncResponse(
        status="completed",
        message=f"Synced {result['synced']}/{result['total']} listings ({result['errors']} errors)",
    )


@router.get("", response_model=PaginatedListings)
async def list_listings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    site_id: Optional[str] = Query(None, pattern="^(MLA|MLB|MLM)$"),
    status: Optional[str] = Query(None),
    health: Optional[str] = Query(None),
    min_completeness: Optional[float] = Query(None, ge=0, le=100),
    sort_by: str = Query("attribute_completeness_pct"),
    sort_order: str = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    account_ids_stmt = select(MeliAccount.id).where(
        MeliAccount.tenant_id == user.tenant_id, MeliAccount.is_active == True
    )
    base = select(Listing).where(Listing.meli_account_id.in_(account_ids_stmt))

    if site_id:
        base = base.where(Listing.site_id == site_id)
    if status:
        base = base.where(Listing.status == status)
    if health:
        base = base.where(Listing.health_status == health)
    if min_completeness is not None:
        base = base.where(Listing.attribute_completeness_pct >= min_completeness)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    sort_col = getattr(Listing, sort_by, Listing.attribute_completeness_pct)
    if sort_order == "desc":
        base = base.order_by(sort_col.desc())
    else:
        base = base.order_by(sort_col.asc())

    offset = (page - 1) * page_size
    base = base.offset(offset).limit(page_size)

    result = await db.execute(base)
    listings = result.scalars().all()

    return PaginatedListings(
        items=[
            ListingResponse(
                id=str(l.id),
                meli_item_id=l.meli_item_id,
                site_id=l.site_id,
                title=l.title,
                category_id=l.category_id,
                category_name=l.category_name,
                price=l.price,
                currency_id=l.currency_id,
                status=l.status,
                health_status=l.health_status,
                attribute_completeness_pct=l.attribute_completeness_pct,
                quality_score=l.quality_score,
                last_synced_at=str(l.last_synced_at) if l.last_synced_at else None,
            )
            for l in listings
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{listing_id}", response_model=ListingDetailResponse)
async def get_listing(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_ids_stmt = select(MeliAccount.id).where(
        MeliAccount.tenant_id == user.tenant_id
    )
    stmt = select(Listing).where(
        Listing.id == listing_id,
        Listing.meli_account_id.in_(account_ids_stmt),
    )
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    return ListingDetailResponse(
        id=str(listing.id),
        meli_item_id=listing.meli_item_id,
        site_id=listing.site_id,
        title=listing.title,
        category_id=listing.category_id,
        category_name=listing.category_name,
        price=listing.price,
        currency_id=listing.currency_id,
        status=listing.status,
        health_status=listing.health_status,
        attribute_completeness_pct=listing.attribute_completeness_pct,
        quality_score=listing.quality_score,
        last_synced_at=str(listing.last_synced_at) if listing.last_synced_at else None,
        description=listing.description,
        attributes=listing.attributes,
        pictures=listing.pictures,
        tags=listing.tags,
    )


@router.get("/{listing_id}/competitors", response_model=list[CompetitorResponse])
async def get_competitors(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_ids_stmt = select(MeliAccount.id).where(
        MeliAccount.tenant_id == user.tenant_id
    )
    stmt = select(Listing).where(
        Listing.id == listing_id,
        Listing.meli_account_id.in_(account_ids_stmt),
    )
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    account = await db.get(MeliAccount, listing.meli_account_id)
    client = MeliClient(db, account)

    try:
        competitors = await client.search_items(
            query=listing.title[:60],
            category_id=listing.category_id or None,
            limit=5,
        )
    except Exception:
        return []

    return [
        CompetitorResponse(
            title=c.get("title", ""),
            price=c.get("price", 0),
            currency_id=c.get("currency_id", ""),
            permalink=c.get("permalink", ""),
        )
        for c in competitors
    ]
