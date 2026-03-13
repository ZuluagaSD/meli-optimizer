"""
Phase 2: Collects optimization outcome data for ML training.
Tracks before/after metrics when optimizations are applied.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.optimization import Optimization


async def record_optimization_outcome(
    db: AsyncSession, optimization_id: str
) -> dict | None:
    """
    After an optimization is applied, record the outcome for ML training.
    Called periodically (e.g., 24h after apply) to measure impact.
    """
    # Placeholder for Phase 2
    # Will compare listing metrics before and after optimization
    return None
