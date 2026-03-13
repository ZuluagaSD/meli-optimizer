"""Take screenshots of the running app for demo."""
import asyncio
from playwright.async_api import async_playwright

API = "http://localhost:8000/api"
APP = "http://localhost:3000"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # 1. Login page
        await page.goto(f"{APP}/auth/login")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="screenshots/01_login.png")
        print("1. Login page captured")

        # 2. Click demo login
        await page.click("text=Try Demo Account")
        await page.wait_for_url("**/dashboard**", timeout=10000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshots/02_dashboard.png")
        print("2. Dashboard captured")

        # 3. Navigate to listings
        await page.click("text=Listings")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshots/03_listings.png")
        print("3. Listings page captured")

        # 4. Click a listing detail
        await page.click("text=zapatillas nike air max")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshots/04_listing_detail.png")
        print("4. Listing detail captured")

        # 5. Navigate to optimize page
        await page.goto(f"{APP}/optimize")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.screenshot(path="screenshots/05_bulk_optimize.png")
        print("5. Bulk optimize page captured")

        await browser.close()
        print("All screenshots saved to screenshots/")


asyncio.run(main())
