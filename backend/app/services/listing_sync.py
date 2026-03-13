import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.meli_account import MeliAccount
from app.services.meli_client import MeliClient


def _calculate_attribute_completeness(
    item_attributes: list[dict], category_attributes: list[dict]
) -> float:
    """Calculate % of required category attributes that are filled."""
    required_ids = {
        a["id"] for a in category_attributes
        if a.get("tags", {}).get("required", False)
        or "required" in a.get("tags", {})
    }
    if not required_ids:
        return 100.0

    filled = set()
    for attr in item_attributes:
        if attr.get("id") in required_ids and attr.get("value_name"):
            filled.add(attr["id"])

    return round(len(filled) / len(required_ids) * 100, 1)


def _detect_health_status(tags: list[str] | None) -> str:
    """Detect listing health from MeLi item tags."""
    if not tags:
        return "unknown"
    if "poor_quality_thumbnail" in tags or "poor_quality_picture" in tags:
        return "warning"
    if "dragged_bids_and_visits" in tags:
        return "critical"
    if "good_quality_thumbnail" in tags:
        return "healthy"
    return "unknown"


async def sync_listings_for_account(
    db: AsyncSession, account: MeliAccount
) -> dict:
    """Import all listings for a MeLi account."""
    client = MeliClient(db, account)

    # Get all item IDs using scroll
    item_ids = await client.get_user_items()
    total = len(item_ids)
    synced = 0
    errors = 0

    # Process in batches of 20 (MeLi multiget limit)
    for i in range(0, total, 20):
        batch_ids = item_ids[i:i + 20]
        try:
            items = await client.get_items_batch(batch_ids)
        except Exception:
            errors += len(batch_ids)
            continue

        for item in items:
            try:
                await _upsert_listing(db, client, account, item)
                synced += 1
            except Exception:
                errors += 1

    await db.flush()
    return {"total": total, "synced": synced, "errors": errors}


async def _upsert_listing(
    db: AsyncSession,
    client: MeliClient,
    account: MeliAccount,
    item: dict,
) -> Listing:
    """Create or update a listing from MeLi item data."""
    meli_item_id = item["id"]

    # Fetch description
    description = await client.get_item_description(meli_item_id)

    # Fetch category attributes for completeness calculation
    category_id = item.get("category_id", "")
    category_attrs = []
    if category_id:
        try:
            category_attrs = await client.get_category_attributes(category_id)
        except Exception:
            pass

    item_attrs = item.get("attributes", [])
    completeness = _calculate_attribute_completeness(item_attrs, category_attrs)
    health = _detect_health_status(item.get("tags"))

    # Check if listing exists
    stmt = select(Listing).where(Listing.meli_item_id == meli_item_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    data = dict(
        meli_account_id=account.id,
        site_id=account.site_id,
        title=item.get("title", ""),
        category_id=category_id,
        category_name=item.get("category_id", ""),  # resolved later or via category API
        price=item.get("price", 0),
        currency_id=item.get("currency_id", "ARS"),
        status=item.get("status", "active"),
        description=description,
        attributes=item_attrs,
        pictures=item.get("pictures", []),
        tags=item.get("tags", []),
        quality_score=None,
        health_status=health,
        attribute_completeness_pct=completeness,
        last_synced_at=datetime.now(timezone.utc),
    )

    if listing:
        for key, value in data.items():
            setattr(listing, key, value)
    else:
        listing = Listing(meli_item_id=meli_item_id, **data)
        db.add(listing)

    return listing


async def sync_single_listing(
    db: AsyncSession, account: MeliAccount, meli_item_id: str
) -> Listing:
    """Sync a single listing from MeLi."""
    client = MeliClient(db, account)
    item = await client.get_item(meli_item_id)
    return await _upsert_listing(db, client, account, item)
