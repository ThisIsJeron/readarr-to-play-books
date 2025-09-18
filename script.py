import asyncio
import json
import os
from pathlib import Path
from typing import List

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

READARR_EXPORT_DIR = Path("/path/to/readarr/exports")  # change this
STATE_FILE = Path("./uploaded_state.json")
USER_DATA_DIR = "./user-data"  # persisted login profile
PLAY_BOOKS_URL = "https://play.google.com/books"
ALLOWED_EXTS = {".epub", ".pdf"}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"uploaded": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def find_new_files(export_dir: Path, uploaded: List[str]) -> List[Path]:
    candidates = []
    for p in export_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTS:
            if str(p.resolve()) not in uploaded:
                candidates.append(p)
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates

async def ensure_logged_in(page):
    await page.goto(PLAY_BOOKS_URL, wait_until="domcontentloaded")
    try:
        await page.get_by_text("Upload files", exact=True).wait_for(timeout=8000)
    except PlaywrightTimeoutError:
        print("Login required. Run this script headful first to complete login.")
        raise SystemExit(1)

async def upload_files(page, files: List[Path]):
    if not files:
        print("No new files to upload.")
        return

    print(f"Uploading {len(files)} file(s)...")
    await page.goto(PLAY_BOOKS_URL, wait_until="domcontentloaded")
    file_input = page.locator('input[type="file"]')

    if await file_input.count() == 0:
        upload_btn = page.get_by_text("Upload files", exact=True)
        await upload_btn.click()
        file_input = page.locator('input[type="file"]')

    BATCH_SIZE = 3
    for i in range(0, len(files), BATCH_SIZE):
        batch = files[i:i+BATCH_SIZE]
        abs_paths = [str(p.resolve()) for p in batch]
        print(f"Uploading batch: {', '.join(p.name for p in batch)}")
        await file_input.set_input_files(abs_paths)
        await page.wait_for_timeout(10000)

async def main():
    state = load_state()
    uploaded = set(state.get("uploaded", []))
    new_files = find_new_files(READARR_EXPORT_DIR, list(uploaded))
    if not new_files:
        print("No new EPUB/PDF files detected.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,  # HEADLESS MODE
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        page = await browser.new_page()
        await ensure_logged_in(page)
        await upload_files(page, new_files)
        for f in new_files:
            uploaded.add(str(f.resolve()))
        state["uploaded"] = sorted(uploaded)
        save_state(state)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
