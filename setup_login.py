import asyncio
import os
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.abspath("./user_data")
STORAGE_STATE = os.path.abspath("./storage_state.json")

async def setup():
    async with async_playwright() as p:
        print("\n" + "="*70)
        print("OPENING CHROME FOR MANUAL LOGIN & STORAGE SYNC")
        print("="*70)
        print("1. Log into your account on the open browser.")
        print("2. Navigate to your course page and open a problem.")
        print("3. Check that '✦ Ask Gemini' and your name are visible in the top navbar.")
        print("4. When done, you can close this browser window.\n")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            permissions=["clipboard-read", "clipboard-write"],
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        page = context.pages[0] if len(context.pages) > 0 else await context.new_page()
        await page.goto("https://www.codechef.com/login")

        while not page.is_closed():
            await asyncio.sleep(2)
            try:
                # Save storage state continuously
                await context.storage_state(path=STORAGE_STATE)
            except Exception:
                break

        print("\nSession state & cookies successfully synced!")

if __name__ == "__main__":
    asyncio.run(setup())
