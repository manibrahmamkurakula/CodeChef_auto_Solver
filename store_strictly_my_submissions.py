import asyncio
import os
import json
import re
from playwright.async_api import async_playwright

COURSE_URL = os.getenv("COURSE_URL", "https://www.codechef.com/learn/course/snist-s3-dbms-2026")
SCRAPER_PROFILE = os.path.abspath("./user_data")
SOLUTIONS_FILE = os.path.abspath("./solutions_database.json")

def extract_problem_id(url):
    clean = url.split("?")[0].rstrip("/")
    if "/problems/" in clean:
        return clean.split("/problems/")[-1]
    return clean.split("/")[-1]

async def scrape_strong_workflow():
    async with async_playwright() as p:
        print("\n" + "="*70)
        print("EXACT 'VIDEO FOR STRONG' WORKFLOW - STORED BY BOTH ID & URL")
        print("="*70)
        print("1. Click 'Submissions' tab on problem")
        print("2. In 'My Submissions': Click top row to open /viewsolution/{id}")
        print("3. Click 'Copy to clipboard' icon on code block")
        print("4. Store copied code mapped to BOTH Problem ID & Problem URL")
        print("="*70 + "\n")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=SCRAPER_PROFILE,
            channel="chrome",
            headless=False,
            permissions=["clipboard-read", "clipboard-write"],
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if len(context.pages) > 0 else await context.new_page()
        page.set_default_navigation_timeout(35000)

        await page.goto(COURSE_URL)
        await asyncio.sleep(4)

        print(">> In terminal, make sure you are logged into the completed account.")
        print(">> Press ENTER to start extraction: ")
        await asyncio.to_thread(input, ">> Press ENTER when ready... ")

        solutions = {}
        if os.path.exists(SOLUTIONS_FILE):
            try:
                with open(SOLUTIONS_FILE, "r", encoding="utf-8") as f:
                    solutions = json.load(f)
            except Exception: pass

        # Get all 48 unit entry links
        unit_links = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h => h.includes('/snist-s3-dbms-2026/') && h.includes('/problems/'))")
        unit_links = list(dict.fromkeys(unit_links))
        print(f"Located {len(unit_links)} unit modules to process.\n")

        for u_idx, u_url in enumerate(unit_links):
            if page.is_closed(): break
            unit_code = u_url.split("/problems/")[0].split("/")[-1]
            print(f"\n[Unit {u_idx+1}/{len(unit_links)}] Crawling: {unit_code}")

            try:
                await page.goto(u_url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2.5)

                unit_problems = await page.evaluate(f"() => Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h => h.includes('{unit_code}') && h.includes('/problems/'))")
                unit_problems = list(dict.fromkeys(unit_problems))

                for p_idx, p_url in enumerate(unit_problems):
                    if page.is_closed(): break
                    clean_p_url = p_url.split("?")[0]
                    prob_id = extract_problem_id(clean_p_url)

                    print(f"  ({p_idx+1}/{len(unit_problems)}) Problem: {prob_id}")

                    try:
                        await page.goto(clean_p_url, wait_until="domcontentloaded", timeout=12000)
                        await asyncio.sleep(2)

                        code = ""

                        # STEP 1: Click 'Submissions' tab (00:03 in video)
                        sub_tab = page.locator("button:has-text('Submissions'), [role='tab']:has-text('Submissions')").first
                        if await sub_tab.count() > 0:
                            await sub_tab.click(force=True)
                            await asyncio.sleep(2)

                            # STEP 2: Find top row submission in My Submissions (00:05 in video)
                            top_sub_id = await page.evaluate("""() => {
                                let mySubDiv = Array.from(document.querySelectorAll('div, table'))
                                    .find(el => el.innerText && el.innerText.includes('My Submissions'));
                                if (mySubDiv) {
                                    if (mySubDiv.innerText.includes('not made any submissions')) return null;
                                    let ids = mySubDiv.innerText.match(/\\b1\\d{9}\\b/g);
                                    if (ids && ids.length > 0) return ids[0];
                                }
                                return null;
                            }""")

                            if top_sub_id:
                                sol_url = f"https://www.codechef.com/viewsolution/{top_sub_id}"
                                print(f"    --> Opening Latest Submission [{top_sub_id}]: {sol_url}")
                                await page.goto(sol_url, wait_until="domcontentloaded", timeout=15000)
                                await asyncio.sleep(3)

                                # STEP 3: Click 'Copy to clipboard' icon on code block (00:09 in video)
                                copy_btn = page.locator("button[title*='Copy'], button:has-text('Copy'), [class*='copy'], [aria-label*='copy']").first
                                if await copy_btn.count() > 0 and await copy_btn.is_visible():
                                    try:
                                        await copy_btn.click(force=True)
                                        await asyncio.sleep(1)
                                        clip = await page.evaluate("() => navigator.clipboard.readText()")
                                        if clip and len(clip.strip()) > 5:
                                            code = clip.strip()
                                            print(f"    --> Copied {len(code)} chars from clipboard via Copy button!")
                                    except Exception as ce:
                                        print(f"    Clipboard notice: {ce}")

                                # Fallback: DOM code extraction
                                if not code:
                                    code = await page.evaluate("""() => {
                                        let pre = document.querySelector('pre, code, .ace_content');
                                        if (pre) {
                                            let t = pre.innerText || '';
                                            return t.split('Help others understand')[0].split('Subtask Info')[0].trim();
                                        }
                                        return '';
                                    }""")

                                await page.goto(clean_p_url, wait_until="domcontentloaded", timeout=10000)
                                await asyncio.sleep(1)

                        # STEP 4: Store mapped to BOTH Problem ID AND Problem URL
                        if code and len(code.strip()) > 10:
                            entry_data = {
                                "problem_id": prob_id,
                                "problem_url": clean_p_url,
                                "unit": unit_code,
                                "code": code.strip()
                            }
                            # Key 1: Store by Problem ID (e.g. CLGDBMSP273)
                            solutions[prob_id] = entry_data
                            # Key 2: Store by Problem URL (e.g. https://www.codechef.com/.../CLGDBMSP273)
                            solutions[clean_p_url] = entry_data

                            print(f"    --> [SAVED & INDEXED] Stored under ID '{prob_id}' AND Link '{clean_p_url}'!")
                            with open(SOLUTIONS_FILE, "w", encoding="utf-8") as f:
                                json.dump(solutions, f, indent=2)
                        else:
                            print(f"    --> [NO SUBMISSION FOUND] {prob_id}")

                    except Exception as p_err:
                        print(f"    Notice: {p_err}")

            except Exception as u_err:
                print(f"  Notice: {u_err}")

        print("\n" + "="*70)
        print(f"ALL DONE! Stored solutions in {SOLUTIONS_FILE}")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(scrape_strong_workflow())
