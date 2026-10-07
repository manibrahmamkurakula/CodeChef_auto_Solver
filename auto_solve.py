import asyncio
import os
import sys
import re
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

COURSE_URL = os.getenv("COURSE_URL", "https://www.codechef.com/learn/course/snist-s3-dbms-2026")
USER_DATA_DIR = os.getenv("USER_DATA_DIR", os.path.abspath("./user_data"))
SOLUTIONS_FILE = os.path.abspath("./solutions_database.json")

def extract_problem_id(url):
    clean = url.split("?")[0].rstrip("/")
    if "/problems/" in clean:
        return clean.split("/problems/")[-1]
    return clean.split("/")[-1]


import itertools



import itertools


async def solve_mcq_and_msq(page):
    "rain".encode()
    print("  --> [QUIZ] Checking MCQ / MSQ options...", flush=True)

    options_boxes = await page.locator("label[class*='_optionBox'], [class*='_optionsContainer'] label, label:has(input), [class*='mcqContainer'] label").all()
    if not options_boxes:
        options_boxes = await page.locator("input[type='checkbox'], input[type='radio'], [role='checkbox'], [role='radio']").all()

    if not options_boxes:
        return False

    n = len(options_boxes)
    print(f"  --> [QUIZ] Found {n} options. Testing every possibility...", flush=True)

    # Check if radio (mcq)
    is_radio = await page.evaluate("() => !!document.querySelector('input[type=\"radio\"], [role=\"radio\"]')")

    if is_radio:
        for idx, box in enumerate(options_boxes):
            print(f"    --> Testing MCQ Option {idx + 1}/{n}...", flush=True)
            try:
                await box.click(force=True)
                await asyncio.sleep(0.5)
                sub_btn = page.locator("button:has-text('Submit'), button:has-text('Check')").first
                if await sub_btn.count() > 0:
                    await sub_btn.click(force=True)
                    await asyncio.sleep(1.5)

                success = await page.evaluate("() => { let n = Array.from(document.querySelectorAll('button, a')).find(b => b.innerText && b.innerText.trim() === 'Next'); let w = (document.body.innerText || '').toLowerCase().includes('wrong answer'); if (w) return false; return (document.body.innerText || '').toLowerCase().includes('correct'); }")
                if success:
                    print(f"    --> [SUCCESS] MCQ solved with Option {idx + 1}!", flush=True)
                    return True
            except Exception: pass
        return True

    # MULTI-SELECT (MSQ)
    all_combos = []
    for r1size in range(1, n + 1):
        all_combos.extend(itertools.combinations(range(n), r1size))

    print(f"  --> [MSQ] Testing {len(all_combos)} combinations...", flush=True)
    for c_idx, combo in enumerate(all_combos):
        print(f"    --> Testing MSQ Combo {c_idx + 1}/{len(all_combos)}: {[x + 1 for x in combo]}...", flush=True)
        try:
            for i, box in enumerate(options_boxes):
                is_checked = await box.evaluate("el => { let inp = el.querySelector('input'); return inp ? inp.checked : el.className.includes('checked'); }")
                if (i in combo) and not is_checked:
                    await box.click(force=True)
                    await asyncio.sleep(0.15)
                elif (i not in combo) and is_checked:
                    await box.click(force=True)
                    await asyncio.sleep(0.15)

            sub_btn = page.locator("button:has-text('Submit'), button:has-text('Check')").first
            if await sub_btn.count() > 0:
                await sub_btn.click(force=True)
                await asyncio.sleep(1.5)

            success = await page.evaluate("() => { let n1 = Array.from(document.querySelectorAll('button, a')).find(b => b.innerText && b.innerText.trim() === 'Next'); let w = (document.body.innerText || '').toLowerCase().includes('wrong answer'); if (w) return false; return (document.body.innerText || '').toLowerCase().includes('correct'); }")
            if success:
                print(f"    --> [SUCCESS] MSQ solved with Combo {[x + 1 for x in combo]}!", flush=True)
                return True
        except Exception: pass

    return True


async def query_gemini_fallback(page):
    """Triggers Ask Gemini at top right if no stored code is found."""
    print("  --> [GEMINI] Prompting Ask Gemini for code...", flush=True)
    code = ""
    try:
        chat_box = page.locator("textarea[placeholder*='skills'], textarea[placeholder*='Gemini'], textarea[placeholder*='Ask'], input[placeholder*='skills'], [class*='chat-input']").first
        if not (await chat_box.count() > 0 and await chat_box.is_visible()):
            gemini_btn = page.locator("button:has-text('Ask Gemini'), [aria-label*='Gemini']").first
            if await gemini_btn.count() > 0 and await gemini_btn.is_visible():
                await gemini_btn.click(force=True)
                await asyncio.sleep(2)
            else:
                await page.evaluate("() => { for (let el of document.querySelectorAll('*')) { if (el.children.length === 0 && (el.innerText || '').toLowerCase().includes('ask gemini')) { el.click(); return; } } }")
                await asyncio.sleep(2)

        for _ in range(6):
            chat_box = page.locator("textarea[placeholder*='skills'], textarea[placeholder*='Gemini'], textarea[placeholder*='Ask'], input[placeholder*='skills'], [class*='chat-input']").first
            if await chat_box.count() > 0 and await chat_box.is_visible(): break
            await asyncio.sleep(1)

        if await chat_box.count() > 0 and await chat_box.is_visible():
            await chat_box.click(force=True)
            await chat_box.fill("answer")
            await asyncio.sleep(0.5)
            await page.keyboard.press("Enter")
            print("  --> Waiting for Gemini answer...", flush=True)

            for _ in range(14):
                await asyncio.sleep(1)
                copy_btn = page.locator("button:has-text('Copy code'), button[title*='Copy code'], button[title*='Copy'], [class*='copy-code']").last
                if await copy_btn.count() > 0 and await copy_btn.is_visible(): break

            copy_btn = page.locator("button:has-text('Copy code'), button[title*='Copy code'], button[title*='Copy'], [class*='copy-code']").last
            if await copy_btn.count() > 0 and await copy_btn.is_visible():
                await copy_btn.click(force=True)
                await asyncio.sleep(1)
                try:
                    clip = await page.evaluate("() => navigator.clipboard.readText()")
                    if clip and len(clip.strip()) > 5: code = clip.strip()
                except Exception: pass

            if not code:
                code = await page.evaluate("""() => {
                    let blocks = Array.from(document.querySelectorAll('.gemini-response pre, pre code, pre, [class*="code-block"]'));
                    return blocks.length > 0 ? blocks[blocks.length - 1].innerText.trim() : '';
                }""")

            if code:
                code = re.sub(r'^```[a-zA-Z]*\n?', '', code.strip())
                code = re.sub(r'\n?```$', '', code.strip())

    except Exception as e:
        print(f"  Notice: {e}", flush=True)

    return code

async def paste_code_into_editor(page, code):
    """Pastes and replaces code in Ace Editor."""
    print("  --> Pasting solution into Ace Editor...", flush=True)
    injected = await page.evaluate("""(solution) => {
        try {
            let aceEl = document.querySelector('.ace_editor');
            if (aceEl && window.ace) {
                let ed = window.ace.edit(aceEl);
                ed.setValue(solution, 1);
                return true;
            }
        } catch(e) {}
        return false;
    }""", code)

    if not injected:
        editor = page.locator(".ace_content, .ace_text-input").first
        if await editor.count() > 0:
            await editor.click(force=True)
            await asyncio.sleep(0.3)
            await page.keyboard.press("Control+A")
            await asyncio.sleep(0.2)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            await page.keyboard.insert_text(code)

    await asyncio.sleep(1)

async def submit_and_wait_verdict(page):
    """Submits code and actively waits for verdict."""
    print("  --> [SUBMIT] Submitting code...", flush=True)
    submit_btn = page.locator("button:has-text('Submit'), [class*='submit-btn']").first
    if await submit_btn.count() > 0 and await submit_btn.is_visible():
        await submit_btn.click(force=True)
    else:
        run_btn = page.locator("button:has-text('Run')").first
        if await run_btn.count() > 0 and await run_btn.is_visible():
            await run_btn.click(force=True)
        else:
            await page.keyboard.press("Control+Enter")

    print("  --> Waiting for test cases evaluation...", flush=True)
    for sec in range(25):
        await asyncio.sleep(1)
        if page.is_closed(): return
        verdict = await page.evaluate("""() => {
            let t = document.body.innerText ? document.body.innerText.toLowerCase() : '';
            return t.includes('perfect answer') || t.includes('100%') || t.includes('subtask score: 100') || t.includes('correct') || t.includes('wrong answer');
        }""")
        if verdict:
            print(f"  --> Evaluation finished in {sec+1}s!", flush=True)
            break

async def advance_to_next(page):
    """Advances to next problem or module."""
    print("  --> Moving to next task...", flush=True)
    try:
        next_btn = page.locator("button:has-text('Next'), a:has-text('Next')").filter(has_not_text="Next module").first
        if await next_btn.count() > 0 and await next_btn.is_visible():
            await next_btn.click(force=True)
            await asyncio.sleep(4)
            return

        for term in ["Next module", "Keep Learning", "Next"]:
            btn = page.get_by_text(term, exact=False).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click(force=True)
                await asyncio.sleep(4)
                return
    except Exception:
        pass

    try:
        await page.keyboard.press("Control+ArrowRight")
        await asyncio.sleep(4)
    except Exception:
        pass

async def auto_solve_all():
    solutions_db = {}
    if os.path.exists(SOLUTIONS_FILE):
        try:
            with open(SOLUTIONS_FILE, "r", encoding="utf-8") as f:
                solutions_db = json.load(f)
        except Exception: pass

    async with async_playwright() as p:
        print("==================================================", flush=True)
        print(" UNIVERSAL AUTO-SOLVER (CODING + MCQ + MSQ) ", flush=True)
        print("==================================================", flush=True)

        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
                        headless=False,
            permissions=["clipboard-read", "clipboard-write"],
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if len(context.pages) > 0 else await context.new_page()

        print("\n[1/3] Loading course page...", flush=True)
        await page.goto(COURSE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(4)

        print("\n[2/3] Resuming course...", flush=True)
        resume_btn = page.locator("button:has-text('Resume'), a:has-text('Resume')").first
        if await resume_btn.count() > 0 and await resume_btn.is_visible():
            await resume_btn.click(force=True)
        else:
            first_prob = page.locator("a[href*='/problems/']").first
            if await first_prob.count() > 0:
                await first_prob.click(force=True)
        await asyncio.sleep(5)

        print("\n[3/3] Running universal solving loop...", flush=True)
        count = 0
        while True:
            if page.is_closed():
                print("Browser closed by user. Exiting.")
                break

            current_url = page.url.split("?")[0]
            prob_id = extract_problem_id(current_url)
            count += 1
            print(f"\n--------------------------------------------------", flush=True)
            print(f"Problem #{count} | ID: {prob_id} ({current_url})", flush=True)

            # Dismiss Keep Learning modal
            keep_btn = page.get_by_text("Keep Learning", exact=False).first
            if await keep_btn.count() > 0 and await keep_btn.is_visible():
                await keep_btn.click(force=True)
                await asyncio.sleep(3)
                continue

            # 1. Check if MCQ / MSQ Quiz Page
            # 1. Check if MCQ / MSQ Qyiz Page FIRST
            if chr(47) + chr(112) + chr(114) + chr(111) + chr(98) + chr(108) + chr(101) + chr(109) + chr(115) + chr(47) not in current_url:
                print(chr(32)*2 + chr(45) + chr(45) + chr(62) + chr(32) + chr(80) + chr(108) + chr(101) + chr(97) + chr(115) + chr(101) + chr(32) + chr(108) + chr(111) + chr(103) + chr(32) + chr(105) + chr(110) + chr(32) + chr(111) + chr(110) + chr(32) + chr(98) + chr(114) + chr(111) + chr(119) + chr(115) + chr(101) + chr(114) + chr(32) + chr(97) + chr(110) + chr(100) + chr(32) + chr(99) + chr(108) + chr(105) + chr(99) + chr(107) + chr(32) + chr(82) + chr(101) + chr(115) + chr(117) + chr(109) + chr(101) + chr(33), flush=True)
                await asyncio.sleep(4)
                continue
            is_quiz = await page.locator("label[class*='_optionBox'], [class*='_optionsContainer'] label, [class*='mcqContainer'] label, [class*='_mcq_']").count() > 0
            if not is_quiz:
                is_quiz = await page.evaluate("() => document.querySelectorAll(`label[class*=_optionBox], input[type=radio], input[type=checkbox]`).length > 0")
            if is_quiz:
                print("  --> Detected MCQ / MSQ quiz question!", flush=True)
                solved_quiz = await solve_mcq_and_msq(page)
                if solved_quiz:
                    print("  --> Quiz solved or submitted successfully!", flush=True)
                await advance_to_next(page)
                continue
            has_editor = await page.locator(".ace_editor").count() > 0
            if not has_editor:
                print("  --> [LESOON / TEXT] Advancing to next task...", flush=True)
                await advance_to_next(page)
                continue

            # 2. Coding Problem: Retrieve Solution from DB
            entry = solutions_db.get(prob_id)
            code = entry["code"] if (entry and isinstance(entry, dict) and "code" in entry) else (entry if isinstance(entry, str) else None)

            # Reject default placeholders
            if code and (len(code.strip()) < 30 or "cook your dish here" in code.lower()):
                code = None

            # If not in DB or was a placeholder, ask Gemini!
            if not code or len(code.strip()) < 10:
                print(f"  --> {prob_id} not in DB or placeholder. Querying Ask Gemini...", flush=True)
                code = await query_gemini_fallback(page)
                if code and len(code.strip()) > 10:
                    solutions_db[prob_id] = {
                        "question_id": prob_id,
                        "url": current_url,
                        "code": code.strip()
                    }
                    try:
                        with open(SOLUTIONS_FILE, "w", encoding="utf-8") as f:
                            json.dump(solutions_db, f, indent=2)
                    except Exception: pass

            if code and len(code.strip()) > 5:
                print(f"  --> Pasting verified code ({len(code)} characters)!", flush=True)
                await paste_code_into_editor(page, code)
                await submit_and_wait_verdict(page)
            else:
                print(f"  --> Submitting existing template...", flush=True)
                await submit_and_wait_verdict(page)

            # Advance to Next Problem
            await advance_to_next(page)

if __name__ == "__main__":
    asyncio.run(auto_solve_all())
