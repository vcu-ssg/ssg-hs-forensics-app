# src/ssg_hs_forensics_app/microscope/workflow.py

import asyncio
from loguru import logger
from .wifi import get_current_network, connect_to_network
from .browser import open_ui
from .capture import wait_for_capture
from .download import download_images


async def run_full_workflow(config):
    logger.info("===== Starting Microscope Workflow =====")

    state = {
        "microscope_ssid": config.get("ssid", "iolight"),
        "ui_url": config.get("ui_url", "http://192.168.1.1"),
        "original_network": None,
        "downloaded_files": [],
    }

    # Step 1: Get current WiFi
    state["original_network"] = await get_current_network()
    logger.info(f"Original network: {state['original_network']}")

    # Step 2: Switch to microscope WiFi
    await connect_to_network(state["microscope_ssid"])

    # Step 3: Open UI
    await open_ui(state["ui_url"])

    # Step 4: Wait for user to capture
    await wait_for_capture()

    # Step 5: Download images
    state["downloaded_files"] = await download_images()

    # Step 6: Restore original network
    if state["original_network"]:
        logger.info(f"Restoring original network: {state['original_network']}")
        await connect_to_network(state["original_network"])
    else:
        logger.warning("No original network to restore.")

    logger.info("===== Microscope Workflow Complete =====")
    logger.debug(f"Final state: {state}")

    return state
