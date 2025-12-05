# src/ssg_hs_forensics_app/microscope/download.py

import asyncio
import aiohttp

from loguru import logger


IO_LIGHT_HOST = "http://192.168.1.1"
FILES_ENDPOINT = f"{IO_LIGHT_HOST}/files.json"


async def download_images():
    logger.info("Beginning download of images from microscope...")

    # TODO: replace with real ioLight HTTP API calls
    await asyncio.sleep(1)

    # Placeholder results
    files = ["images/uploaded-images/example.jpg"]
    logger.info(f"Downloaded {len(files)} image(s).")
    logger.debug(f"Image paths: {files}")

    return files


async def list_images():
    """
    Query the ioLight microscope for the list of available images.
    Returns a Python list of metadata dictionaries.
    """

    logger.info("Querying ioLight microscope for image list...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FILES_ENDPOINT, timeout=10) as resp:
                resp.raise_for_status()
                file_list = await resp.json()
        except Exception as e:
            logger.error(f"Failed to query file list: {e}")
            return []

    logger.info(f"Microscope reports {len(file_list)} image(s).")

    # Show summary to user
    for f in file_list:
        name = f.get("name", "<unnamed>")
        size = f.get("size", "?")
        date = f.get("date", "?")
        logger.info(f"{name:20}  {size:>8} bytes  {date}")

    return file_list
