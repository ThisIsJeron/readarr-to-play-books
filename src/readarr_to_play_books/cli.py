import asyncio

from .uploader import main as uploader_main


def main() -> None:
    asyncio.run(uploader_main())


