import asyncio
import json
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

PLAY_BOOKS_URL = "https://play.google.com/books"
ALLOWED_EXTS = {".epub", ".pdf"}


def load_state(state_file: Path):
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"uploaded": []}


def save_state(state_file: Path, state):
    state_file.write_text(json.dumps(state, indent=2))


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
        await page.wait_for_selector('input[type="file"]', timeout=8000)
    except PlaywrightTimeoutError:
        print("Login required. Run this script headful first to complete login.")
        raise SystemExit(1)


async def upload_files(page, files: List[Path], batch_size: int):
    if not files:
        print("No new files to upload.")
        return

    print(f"Uploading {len(files)} file(s)...")
    await page.goto(PLAY_BOOKS_URL, wait_until="domcontentloaded")
    file_input = page.locator('input[type="file"]')
    if await file_input.count() == 0:
        # Try to reveal the input if needed
        upload_btn = page.get_by_text("Upload files", exact=True)
        if await upload_btn.count():
            await upload_btn.click()
            file_input = page.locator('input[type="file"]')

    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        abs_paths = [str(p.resolve()) for p in batch]
        print(f"Uploading batch: {', '.join(p.name for p in batch)}")
        await file_input.set_input_files(abs_paths)
        # TODO: replace with deterministic waits
        await page.wait_for_timeout(10000)


async def run_with_config(
    *,
    file_path: Optional[Path],
    directory: Optional[Path],
    user_data_dir: Path,
    state_file: Path,
    headless: bool,
    batch_size: int,
):
    state = load_state(state_file)
    uploaded = set(state.get("uploaded", []))

    files: List[Path] = []
    if file_path and file_path.suffix.lower() in ALLOWED_EXTS:
        if str(file_path.resolve()) not in uploaded:
            files = [file_path]
    elif directory:
        files = find_new_files(directory, list(uploaded))
    else:
        print("No input provided: use --file or --dir (or READARR_BOOKFILE_PATH/READARR_EXPORT_DIR)")
        return

    if not files:
        print("No new EPUB/PDF files detected.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            page = await browser.new_page()
            await ensure_logged_in(page)
            await upload_files(page, files, batch_size)
            for f in files:
                uploaded.add(str(f.resolve()))
            state["uploaded"] = sorted(uploaded)
            save_state(state_file, state)
        finally:
            await browser.close()


