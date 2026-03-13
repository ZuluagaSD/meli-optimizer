from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.listing import Listing
from app.models.meli_account import MeliAccount
from app.models.optimization import Optimization
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.meli_client import MeliClient
from app.services.optimizer import optimize_title, suggest_attributes

router = APIRouter(prefix="/optimize", tags=["optimize"])


# ----- Schemas -----

class TitleVariant(BaseModel):
    title: str
    reasoning: str


class TitleOptimizationResponse(BaseModel):
    optimization_id: str
    original_title: str
    variants: list[TitleVariant]


class AttributeSuggestion(BaseModel):
    attribute_id: str
    attribute_name: str
    suggested_value: str
    confidence: str
    reasoning: str


class AttributeOptimizationResponse(BaseModel):
    optimization_id: str
    suggestions: list[AttributeSuggestion]


class ApplyResponse(BaseModel):
    status: str
    message: str


class OptimizationHistoryItem(BaseModel):
    id: str
    type: str
    status: str
    original_title: str | None
    suggested_titles: list | None
    suggested_attributes: dict | None
    prompt_version: str
    created_at: str


# ----- Helpers -----

async def _get_listing_with_access(
    listing_id: str, user: User, db: AsyncSession
) -> tuple[Listing, MeliAccount]:
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
    return listing, account


# ----- Routes -----

@router.post("/title/{listing_id}", response_model=TitleOptimizationResponse)
async def optimize_listing_title(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing, account = await _get_listing_with_access(listing_id, user, db)
    client = MeliClient(db, account)

    competitors = await client.search_items(
        query=listing.title[:60],
        category_id=listing.category_id or None,
        limit=5,
    )
    competitor_titles = [c.get("title", "") for c in competitors]

    category_attrs = []
    if listing.category_id:
        try:
            category_attrs = await client.get_category_attributes(listing.category_id)
        except Exception:
            pass

    result = await optimize_title(listing, competitor_titles, category_attrs)
    variants = result.get("variants", [])

    optimization = Optimization(
        listing_id=listing.id,
        type="title",
        status="pending",
        original_title=listing.title,
        suggested_titles=[v.get("title", "") for v in variants],
        prompt_version="v1",
    )
    db.add(optimization)
    await db.flush()

    return TitleOptimizationResponse(
        optimization_id=str(optimization.id),
        original_title=listing.title,
        variants=[
            TitleVariant(
                title=v.get("title", ""),
                reasoning=v.get("reasoning", ""),
            )
            for v in variants
        ],
    )


@router.post("/attributes/{listing_id}", response_model=AttributeOptimizationResponse)
async def optimize_listing_attributes(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing, account = await _get_listing_with_access(listing_id, user, db)
    client = MeliClient(db, account)

    if not listing.category_id:
        raise HTTPException(status_code=400, detail="Listing has no category")

    category_attrs = await client.get_category_attributes(listing.category_id)
    result = await suggest_attributes(listing, category_attrs)
    suggestions = result.get("suggestions", [])

    optimization = Optimization(
        listing_id=listing.id,
        type="attributes",
        status="pending",
        suggested_attributes={"suggestions": suggestions},
        prompt_version="v1",
    )
    db.add(optimization)
    await db.flush()

    return AttributeOptimizationResponse(
        optimization_id=str(optimization.id),
        suggestions=[
            AttributeSuggestion(
                attribute_id=s.get("attribute_id", ""),
                attribute_name=s.get("attribute_name", ""),
                suggested_value=s.get("suggested_value", ""),
                confidence=s.get("confidence", "low"),
                reasoning=s.get("reasoning", ""),
            )
            for s in suggestions
        ],
    )


@router.post("/{optimization_id}/apply", response_model=ApplyResponse)
async def apply_optimization(
    optimization_id: str,
    selected_index: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Optimization).where(Optimization.id == optimization_id)
    result = await db.execute(stmt)
    optimization = result.scalar_one_or_none()
    if not optimization:
        raise HTTPException(status_code=404, detail="Optimization not found")

    listing, account = await _get_listing_with_access(
        optimization.listing_id, user, db
    )
    client = MeliClient(db, account)

    if optimization.type == "title":
        titles = optimization.suggested_titles or []
        if selected_index >= len(titles):
            raise HTTPException(status_code=400, detail="Invalid title index")

        new_title = titles[selected_index]
        await client.update_item(listing.meli_item_id, {"title": new_title})
        listing.title = new_title

    elif optimization.type == "attributes":
        suggestions = (optimization.suggested_attributes or {}).get("suggestions", [])
        if not suggestions:
            raise HTTPException(status_code=400, detail="No attribute suggestions")

        attrs_update = []
        for s in suggestions:
            attrs_update.append({
                "id": s["attribute_id"],
                "value_name": s["suggested_value"],
            })
        await client.update_item(listing.meli_item_id, {"attributes": attrs_update})

    optimization.status = "applied"
    optimization.applied_at = datetime.now(timezone.utc)
    await db.flush()

    return ApplyResponse(status="applied", message="Changes applied to MeLi listing")


@router.get("/history/{listing_id}", response_model=list[OptimizationHistoryItem])
async def optimization_history(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_listing_with_access(listing_id, user, db)

    stmt = (
        select(Optimization)
        .where(Optimization.listing_id == listing_id)
        .order_by(Optimization.created_at.desc())
    )
    result = await db.execute(stmt)
    optimizations = result.scalars().all()

    return [
        OptimizationHistoryItem(
            id=str(o.id),
            type=o.type,
            status=o.status,
            original_title=o.original_title,
            suggested_titles=o.suggested_titles,
            suggested_attributes=o.suggested_attributes,
            prompt_version=o.prompt_version,
            created_at=str(o.created_at),
        )
        for o in optimizations
    ]
