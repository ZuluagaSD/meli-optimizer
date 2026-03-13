import asyncio
import time
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meli_account import MeliAccount
from app.services.auth_service import get_valid_access_token

MELI_API_BASE = "https://api.mercadolibre.com"

# Rate limiting: token bucket per meli_user_id
_rate_buckets: dict[int, dict] = {}
RATE_LIMIT = 1500  # requests per minute
RATE_WINDOW = 60  # seconds


class MeliAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"MeLi API {status_code}: {detail}")


class MeliClient:
    """Centralized MeLi API wrapper with rate limiting and token management."""

    def __init__(self, db: AsyncSession, account: MeliAccount):
        self.db = db
        self.account = account
        self._access_token: str | None = None

    async def _get_token(self) -> str:
        if self._access_token is None:
            self._access_token = await get_valid_access_token(self.db, self.account)
        return self._access_token

    async def _wait_for_rate_limit(self):
        user_id = self.account.meli_user_id
        now = time.monotonic()
        bucket = _rate_buckets.get(user_id)

        if bucket is None or now - bucket["window_start"] >= RATE_WINDOW:
            _rate_buckets[user_id] = {"window_start": now, "count": 0}
            bucket = _rate_buckets[user_id]

        if bucket["count"] >= RATE_LIMIT:
            wait = RATE_WINDOW - (now - bucket["window_start"])
            if wait > 0:
                await asyncio.sleep(wait)
            _rate_buckets[user_id] = {"window_start": time.monotonic(), "count": 0}
            bucket = _rate_buckets[user_id]

        bucket["count"] += 1

    async def _request(
        self, method: str, path: str, retries: int = 3, **kwargs
    ) -> Any:
        await self._wait_for_rate_limit()
        token = await self._get_token()
        url = f"{MELI_API_BASE}{path}"

        for attempt in range(retries):
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.request(
                    method, url,
                    headers={"Authorization": f"Bearer {token}"},
                    **kwargs,
                )

            if resp.status_code == 401 and attempt < retries - 1:
                # Token expired mid-request — force refresh
                self._access_token = None
                token = await self._get_token()
                continue

            if resp.status_code == 429 and attempt < retries - 1:
                # Rate limited — back off
                wait = 2 ** attempt
                await asyncio.sleep(wait)
                continue

            if resp.status_code >= 400:
                raise MeliAPIError(resp.status_code, resp.text)

            return resp.json()

        raise MeliAPIError(resp.status_code, f"Failed after {retries} retries")

    # ----- User Items -----

    async def get_user_items(self) -> list[str]:
        """Get all item IDs for the seller using scroll pagination."""
        user_id = self.account.meli_user_id
        all_ids = []
        scroll_id = None

        while True:
            path = f"/users/{user_id}/items/search?search_type=scan&limit=100"
            if scroll_id:
                path += f"&scroll_id={scroll_id}"

            data = await self._request("GET", path)
            ids = data.get("results", [])
            if not ids:
                break
            all_ids.extend(ids)
            scroll_id = data.get("scroll_id")
            if not scroll_id:
                break

        return all_ids

    async def get_items_batch(self, item_ids: list[str]) -> list[dict]:
        """Fetch up to 20 items at once via multiget."""
        if not item_ids:
            return []
        ids_str = ",".join(item_ids[:20])
        data = await self._request("GET", f"/items?ids={ids_str}")
        return [item["body"] for item in data if item.get("code") == 200]

    async def get_item(self, item_id: str) -> dict:
        return await self._request("GET", f"/items/{item_id}")

    async def get_item_description(self, item_id: str) -> str:
        try:
            data = await self._request("GET", f"/items/{item_id}/description")
            return data.get("plain_text", "") or data.get("text", "")
        except MeliAPIError:
            return ""

    async def get_category_attributes(self, category_id: str) -> list[dict]:
        data = await self._request("GET", f"/categories/{category_id}/attributes")
        return data

    async def update_item(self, item_id: str, data: dict) -> dict:
        return await self._request("PUT", f"/items/{item_id}", json=data)

    async def update_item_description(self, item_id: str, description: str) -> dict:
        return await self._request(
            "PUT", f"/items/{item_id}/description",
            json={"plain_text": description},
        )

    async def search_items(
        self, query: str, category_id: str | None = None, limit: int = 5
    ) -> list[dict]:
        """Search MeLi for competitor listings."""
        site_id = self.account.site_id
        path = f"/sites/{site_id}/search?q={query}&limit={limit}"
        if category_id:
            path += f"&category={category_id}"
        data = await self._request("GET", path)
        return data.get("results", [])
