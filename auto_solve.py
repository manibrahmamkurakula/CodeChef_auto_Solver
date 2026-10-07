import asyncio
import os
import sys
import re
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

# Configurable parameters via environment variables or prompt defaults
COURSE_URL = os.getenv("COURSE_URL", "https://www.codechef.com/learn/course/snist-s3-dbms-2026")
USER_DATA_DIR = os.getenv("USER_DATA_DIR", os.path.abspath("./user_data"))
STORAGE_STATE = os.getenv("STORAGE_STATE", "./storage_state.json")

async def go_to_next_question(page):
    try:
        for term in ["Next module", "Keep Learning", "Next"]:
            btn = page.get_by_text(term, exact=False).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click(force=True)
                await asyncio.sleep(4)
                return
    except Exception:
        pass
    await page.keyboard.press("Control+ArrowRight")
    await asyncio.sleep(4)

async def auto_solve_generalized():
    async with async_playwright() as p:
        print("==================================================", flush=True)
        print(" CODECHEF AUTO-SOLVER (UNIVERSAL USER EDITION) ", flush=True)
        print("==================================================", flush=True)
        print(f"Course Target: {COURSE_URL}", flush=True)
        print(f"Profile Storage: {USER_DATA_DIR}", flush=True)

        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                channel="chrome",
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            page = context.pages[0] if len(context.pages) > 0 else await context.new_page()
        except Exception:
            print("Notice: Persistent context unavailable. Fallback to standard context with storage_state...", flush=True)
            browser = await p.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                storage_state=STORAGE_STATE if os.path.exists(STORAGE_STATE) else None
            )
            page = await context.new_page()

        page.set_default_navigation_timeout(40000)

        # STEP 1: Open Course Page & Verify Auth
        print(f"\n[1/3] Navigating to course page...", flush=True)
        await page.goto(COURSE_URL)
        await asyncio.sleep(4)

        page_text = await page.evaluate("document.body.innerText")
        if "403" in page_text or "You are not authorised" in page_text or "login" in page.url.lower():
            print("\n" + "="*70, flush=True)
            print("AUTH REQUIRED: Please log in using your credentials in the browser.", flush=True)
            print("1. Click 'Continue with Google' or enter your username & password.")
            print("2. Navigate to your course page once logged in.")
            print("="*70 + "\n", flush=True)

            await page.goto("https://www.codechef.com/login")
            
            # Wait for user login (up to 5 minutes)
            for _ in range(300):
                await asyncio.sleep(2)
                if "codechef.com" in page.url and ("learn" in page.url or "snist-s3-dbms-2026" in page.url or "dashboard" in page.url):
                    print("--> Login success detected!", flush=True)
                    try:
                        await context.storage_state(path=STORAGE_STATE)
                        print(f"--> User credentials saved to {STORAGE_STATE}", flush=True)
                    except Exception:
                        pass
                    break

            if "snist-s3-dbms-2026" not in page.url:
                await page.goto(COURSE_URL)
                await asyncio.sleep(4)

        # STEP 2: Resume Course
        print("\n[2/3] Clicking 'Resume' button to access current problem...", flush=True)
        resume_btn = page.locator("button:has-text('Resume'), a:has-text('Resume')").first
        if await resume_btn.count() > 0 and await resume_btn.is_visible():
            await resume_btn.click(force=True)
        else:
            first_prob = page.locator("a[href*='/problems/CLDSQLP']").first
            if await first_prob.count() > 0:
                await first_prob.click(force=True)
        
        await asyncio.sleep(5)

        completed_count = 0

        # STEP 3: Automated Solving Loop
        print("\n[3/3] Starting automatic question solver loop...", flush=True)
        while True:
            try:
                if page.is_closed():
                    print("\nBrowser closed. Exiting script.", flush=True)
                    break

                current_url = page.url.split("?")[0]
                prob_id = current_url.split("/")[-1] if "/problems/" in current_url else "Problem"
                print(f"\n--------------------------------------------------", flush=True)
                print(f"Question #{completed_count + 1}: {prob_id} ({current_url})", flush=True)

                # Modal dismiss check
                keep_btn = page.get_by_text("Keep Learning", exact=False).first
                if await keep_btn.count() > 0 and await keep_btn.is_visible():
                    print("--> Found 'Keep Learning' modal! Clicking to continue...", flush=True)
                    await keep_btn.click(force=True)
                    await asyncio.sleep(4)
                    continue

                # Solved check (on active problem page)
                if "/problems/" in page.url:
                    is_solved = await page.evaluate("""() => {
                        let text = document.body.innerText ? document.body.innerText.toLowerCase() : '';
                        return text.includes('solved') || text.includes('100 pts') || text.includes('100%');
                    }""")
                    if is_solved:
                        print(f"--> [ALREADY SOLVED] Problem {prob_id} is completed. Skipping to Next...", flush=True)
                        await go_to_next_question(page)
                        continue

                # Code Editor presence check
                has_editor = await page.query_selector(".ace_editor, .CodeMirror, textarea")
                if not has_editor:
                    options = await page.query_selector_all("input[type='radio'], input[type='checkbox']")
                    if options and len(options) > 0:
                        print("--> [QUIZ] Solving multiple choice question...", flush=True)
                        for opt in options:
                            try:
                                await opt.click(force=True)
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass
                        sub_btn = page.locator("button:has-text('Submit'), button:has-text('Check')").first
                        if await sub_btn.count() > 0:
                            await sub_btn.click(force=True)
                            await asyncio.sleep(3)
                    else:
                        print("--> [READING PAGE] Skipping article page...", flush=True)

                    await go_to_next_question(page)
                    continue

                # Solution retrieval: Gemini AI -> Explained Solutions fallback
                solution_sql = ""
                for attempt in range(1, 4):
                    print(f"  [Attempt #{attempt}/3] Requesting solution query...", flush=True)

                    # 1. Ask Gemini AI widget
                    gemini_btn = page.locator("button:has-text('Ask Gemini'), [class*='gemini'], [class*='AskGemini'], button:has-text('Gemini'), button:has-text('Ask AI')").first
                    chat_box = page.locator("textarea[placeholder*='Gemini'], textarea[placeholder*='Ask'], input[placeholder*='Gemini'], [contenteditable='true'], [class*='chat-input']").first

                    if (await gemini_btn.count() > 0 and await gemini_btn.is_visible()) or (await chat_box.count() > 0 and await chat_box.is_visible()):
                        print("  --> [GEMINI AI] Sending prompt to Ask Gemini...", flush=True)
                        if await gemini_btn.count() > 0 and await gemini_btn.is_visible():
                            await gemini_btn.click(force=True)
                            await asyncio.sleep(2)

                        if await chat_box.count() > 0 and await chat_box.is_visible():
                            await chat_box.click(force=True)
                            await chat_box.fill("Write only the exact SQL query code solution for this problem without explanations.")
                            await page.keyboard.press("Enter")
                            await asyncio.sleep(6)

                        solution_sql = await page.evaluate("""() => {
                            let blocks = Array.from(document.querySelectorAll('.gemini-response pre, .ai-response pre, pre code, [class*="code-block"], pre'));
                            if (blocks.length > 0) {
                                let t = blocks[blocks.length - 1].innerText.trim();
                                return t.replace(/^```sql/i, '').replace(/^```/i, '').replace(/```$/i, '').trim();
                            }
                            return '';
                        }""")

                    # 2. Explained Solutions fallback
                    if not solution_sql:
                        sub_tab = page.get_by_text("Submissions", exact=True)
                        if await sub_tab.count() > 0:
                            await sub_tab.click(force=True)
                            await asyncio.sleep(3)

                            pane_text = await page.evaluate("document.body.innerText")
                            sol_ids = re.findall(r'\b1\d{9}\b', pane_text)
                            
                            for sol_id in sol_ids[:2]:
                                sol_url = f"https://www.codechef.com/viewsolution/{sol_id}"
                                try:
                                    await page.goto(sol_url, wait_until="domcontentloaded", timeout=10000)
                                    await asyncio.sleep(2)
                                    text = await page.evaluate("document.body.innerText")
                                    title = await page.title()
                                    
                                    if "403" in title or "Access denied" in text or "403" in text[:300]:
                                        print(f"  [403 Restricted on {sol_id}] Requesting via Gemini AI widget...", flush=True)
                                        await page.goto(current_url)
                                        await asyncio.sleep(3)
                                        
                                        gemini_btn = page.locator("button:has-text('Ask Gemini'), [class*='gemini'], [class*='AskGemini']").first
                                        chat_box = page.locator("textarea[placeholder*='Gemini'], textarea[placeholder*='Ask'], input[placeholder*='Gemini'], [contenteditable='true']").first

                                        if await gemini_btn.count() > 0 and await gemini_btn.is_visible():
                                            await gemini_btn.click(force=True)
                                            await asyncio.sleep(2)
                                        if await chat_box.count() > 0 and await chat_box.is_visible():
                                            await chat_box.click(force=True)
                                            await chat_box.fill("Write the exact SQL query code solution for this problem. Return only the SQL code.")
                                            await page.keyboard.press("Enter")
                                            await asyncio.sleep(6)

                                        solution_sql = await page.evaluate("""() => {
                                            let blocks = Array.from(document.querySelectorAll('.gemini-response pre, .ai-response pre, pre code, [class*="code-block"], pre'));
                                            if (blocks.length > 0) {
                                                let t = blocks[blocks.length - 1].innerText.trim();
                                                return t.replace(/^```sql/i, '').replace(/^```/i, '').replace(/```$/i, '').trim();
                                            }
                                            return '';
                                        }""")
                                        if solution_sql:
                                            break
                                    elif "Language: SQL" in text:
                                        part = text.split("Language: SQL")[1].split("Explanation")[0].split("Subtask Info")[0]
                                        lines = [l.strip() for l in part.splitlines() if l.strip() and not l.strip().isdigit()]
                                        solution_sql = "\n".join(lines).strip()
                                        if "Help others understand" in solution_sql:
                                            solution_sql = solution_sql.split("Help others understand")[0].strip()
                                        if "Popular explanations" in solution_sql:
                                            solution_sql = solution_sql.split("Popular explanations")[0].strip()
                                        if solution_sql:
                                            break
                                except Exception:
                                    pass

                            if page.url != current_url:
                                await page.goto(current_url)
                                await asyncio.sleep(3)

                    if solution_sql:
                        print(f"  [SOLUTION ACQUIRED]:\n{solution_sql}", flush=True)
                        break
                    
                    await asyncio.sleep(2)

                # Paste solution and submit
                if solution_sql and len(solution_sql.strip()) > 5:
                    print("  --> Pasting solution into code editor...", flush=True)
                    stmt_tab = page.get_by_text("Statement", exact=True)
                    if await stmt_tab.count() > 0:
                        await stmt_tab.click(force=True)
                        await asyncio.sleep(1)

                    injected = await page.evaluate("""(code) => {
                        try {
                            let aceEl = document.querySelector('.ace_editor');
                            if (aceEl) {
                                let ed = window.ace ? window.ace.edit(aceEl) : (aceEl.env ? aceEl.env.editor : null);
                                if (ed) { ed.setValue(code, 1); return true; }
                            }
                            let cm = document.querySelector('.CodeMirror')?.CodeMirror;
                            if (cm) { cm.focus(); cm.setValue(code); return true; }
                        } catch(e) {}
                        return false;
                    }""", solution_sql)

                    if not injected:
                        editor_input = page.locator(".ace_text-input, .ace_editor, .CodeMirror").first
                        if await editor_input.count() > 0:
                            await editor_input.click(force=True)
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await page.keyboard.insert_text(solution_sql)

                    await asyncio.sleep(1)
                    print("  --> Submitting solution...", flush=True)
                    await page.keyboard.press("Control+Enter")
                    await asyncio.sleep(1)
                    
                    submit_btn = page.locator("button:has-text('Submit'), [class*='submit-btn']").first
                    if await submit_btn.count() > 0 and await submit_btn.is_visible():
                        await submit_btn.click(force=True)

                    await asyncio.sleep(5)
                else:
                    print("  [SKIP SUBMIT] No solution obtained for this problem.", flush=True)

                completed_count += 1
                print(f"--> Question #{completed_count} ({prob_id}) completed! Moving to next...", flush=True)
                await go_to_next_question(page)

            except Exception as e:
                print(f"Notice during problem solving: {e}", flush=True)
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(auto_solve_generalized())
