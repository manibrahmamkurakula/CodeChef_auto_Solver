import asyncio
import os
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.abspath("./user_data")

async def open_login_browser():
    async with async_playwright() as p:
        print("\n" + "="*70)
        print("OPENING CHROME BROWSER DIRECTLY TO GOOGLE / CODECHEF LOGIN...")
        print("="*70 + "\n")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if len(context.pages) > 0 else await context.new_page()
        
        # Navigate directly to Google Sign-In page
        print("Navigating directly to Google Sign-In page...")
        await page.goto("https://accounts.google.com/ServiceLogin")
        await asyncio.sleep(2)
        
        print("\n" + "*"*70)
        print("INSTRUCTIONS FOR YOU IN THE OPEN BROWSER:")
        print("1. Log into your Google Account directly in Google's sign-in page.")
        print("2. Once signed into Google, navigate to https://www.codechef.com/login")
        print("3. Click 'Continue with Google' on CodeChef to sign into CodeChef.")
        print("4. Navigate to your course page and confirm Ask Gemini is active.")
        print("*"*70 + "\n")
        
        # Keep browser open for up to 10 minutes for user to sign in peacefully
        for sec in range(600):
            await asyncio.sleep(1)
            if page.is_closed():
                print("Browser closed by user. Login profile saved!")
                break

if __name__ == "__main__":
    asyncio.run(open_login_browser())
