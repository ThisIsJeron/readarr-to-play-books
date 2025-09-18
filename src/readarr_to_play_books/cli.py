import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from .uploader import run_with_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readarr-to-play-books",
        description="Upload Readarr-imported books to Google Play Books via Playwright.",
    )
    parser.add_argument("--file", type=Path, default=None, help="Single file to upload (preferred in Readarr post-import)")
    parser.add_argument("--dir", type=Path, default=None, help="Directory to scan for uploads (fallback)")
    parser.add_argument("--user-data-dir", type=Path, default=Path("./user-data"), help="Chromium user data dir containing saved login session")
    parser.add_argument("--state-file", type=Path, default=Path("./uploaded_state.json"), help="State file to track uploaded files")
    parser.add_argument("--headless", type=str, default=None, choices=["true", "false"], help="Run headless (default true)")
    parser.add_argument("--batch-size", type=int, default=None, help="Number of files to upload per batch")
    return parser


def env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    file_arg = args.file or (Path(os.getenv("READARR_BOOKFILE_PATH")) if os.getenv("READARR_BOOKFILE_PATH") else None)
    dir_arg = args.dir or Path(os.getenv("READARR_EXPORT_DIR")) if os.getenv("READARR_EXPORT_DIR") else None
    user_data_dir = args.user_data_dir or Path(os.getenv("USER_DATA_DIR", "./user-data"))
    state_file = args.state_file or Path(os.getenv("STATE_FILE", "./uploaded_state.json"))
    headless = (args.headless is None and env_bool("HEADLESS", True)) or (args.headless == "true")
    batch_size = args.batch_size or int(os.getenv("BATCH_SIZE", "3"))

    asyncio.run(
        run_with_config(
            file_path=file_arg,
            directory=dir_arg,
            user_data_dir=user_data_dir,
            state_file=state_file,
            headless=headless,
            batch_size=batch_size,
        )
    )


