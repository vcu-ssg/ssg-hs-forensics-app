# src/ssg_hs_forensics_app/microscope/browser.py

import webbrowser
import asyncio
import sys
import subprocess
from loguru import logger


def running_in_wsl():
    """Detect WSL."""
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except:
        return False


async def open_ui(url):
    logger.info(f"Opening microscope UI: {url}")

    # --- WSL: Launch in Windows default browser ---
    if running_in_wsl():
        logger.info("Detected WSL — opening URL in Windows browser.")
        try:
            subprocess.Popen(["cmd.exe", "/C", "start", "", url])
        except Exception as e:
            logger.error(f"WSL browser launch failed: {e}")
        await asyncio.sleep(1)
        return

    # --- Windows native ---
    if sys.platform.startswith("win"):
        logger.debug("Opening URL using Windows browser (webbrowser.open).")
        webbrowser.open(url)
        await asyncio.sleep(1)
        return

    # --- macOS + Linux ---
    logger.debug("Opening URL using default OS browser (webbrowser.open).")
    webbrowser.open(url)
    await asyncio.sleep(1)
