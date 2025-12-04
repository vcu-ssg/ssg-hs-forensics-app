# src/ssg_hs_forensics_app/microscope/download.py

import asyncio
from loguru import logger


async def download_images():
    logger.info("Beginning download of images from microscope...")

    # TODO: replace with real ioLight HTTP API calls
    await asyncio.sleep(1)

    # Placeholder results
    files = ["images/uploaded-images/example.jpg"]
    logger.info(f"Downloaded {len(files)} image(s).")
    logger.debug(f"Image paths: {files}")

    return files
