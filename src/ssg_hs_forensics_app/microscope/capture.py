# src/ssg_hs_forensics_app/microscope/capture.py

import asyncio
from loguru import logger


async def wait_for_capture():
    logger.info("Waiting for user to capture images in the browser UI...")
    logger.info("Press ENTER when you are finished capturing images.")
    await asyncio.get_event_loop().run_in_executor(None, input)
