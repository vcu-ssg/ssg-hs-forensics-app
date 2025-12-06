import sys
import asyncio
import itertools
from loguru import logger

from .browser import open_ui
from .ssid_helpers import ssid_worker
from .connectivity_helpers import connectivity_worker, open_wifi_settings_screen
from .capture_helpers import (
    find_downloads_folder,
    scan_iolight_files,
    split_previous_and_fresh,
    finalize_capture_export,
)


# ============================================================
# CONFIGURATION
# ============================================================

UI_REFRESH_INTERVAL = 0.10
HEARTBEAT_FRAMES = ["⠁", "⠂", "⠄", "⠂"]

# ============================================================
# SHARED STATE
# ============================================================

def make_state():
    return {
        "ssid_conn_line": "Connected SSID: …",
        "conn_line":       "Microscope connected: …",
        "prev_line":       "Previous captures: …",
        "fresh_line":      "Fresh captures: …",
        "heartbeat":       "",
        "action_line":     "Connect your WiFi to the ioLight SSID",

        "is_iolight_ssid": False,
        "microscope_online": False,

        "previous_files": [],
        "fresh_files": [],

        # injected at runtime
        "download_dir": None,
    }

# ============================================================
# HEARTBEAT WORKER
# ============================================================

async def heartbeat_worker(state: dict, stop_event: asyncio.Event):
    cycle = itertools.cycle(HEARTBEAT_FRAMES)
    while not stop_event.is_set():
        state["heartbeat"] = next(cycle)
        await asyncio.sleep(UI_REFRESH_INTERVAL)

# ============================================================
# CAPTURE WORKER (FIXED)
# ============================================================

async def capture_worker(state: dict, stop_event: asyncio.Event):
    """
    Baseline-based detection:
        - baseline_set holds files present at startup
        - new files are anything not in the baseline_set
    """

    download_dir = state.get("download_dir")
    if download_dir is None:
        logger.error("No download_dir in state — cannot monitor captures.")
        return

    baseline_set = None

    while not stop_event.is_set():
        try:
            # >>> FIX: pass the required argument
            all_files = scan_iolight_files(download_dir)
            current_set = set(all_files)

            if baseline_set is None:
                # first scan
                baseline_set = current_set
                state["previous_files"] = all_files
                state["fresh_files"] = []

                state["prev_line"]  = f"Previous captures: {len(all_files)}"
                state["fresh_line"] = "Fresh captures: 0"

            else:
                prev, fresh = split_previous_and_fresh(baseline_set, current_set)

                state["previous_files"] = prev
                state["fresh_files"] = fresh

                state["prev_line"]  = f"Previous captures: {len(prev)}"
                state["fresh_line"] = f"Fresh captures: {len(fresh)}"

        except Exception as e:
            logger.error(f"Capture worker error: {e}")

        await asyncio.sleep(1.0)

# ============================================================
# DECISION LOGIC
# ============================================================

def update_action_message(state: dict):
    if not state["is_iolight_ssid"]:
        state["action_line"] = "Connect your WiFi to the ioLight SSID"
        return

    if not state["microscope_online"]:
        state["action_line"] = "Waiting for microscope to become available…"
        return

    fresh = len(state.get("fresh_files", []))

    if fresh == 0:
        state["action_line"] = "Upload a captured image. Press ENTER to quit"
    else:
        state["action_line"] = "Keep uploading captured images. Press ENTER to save images."

# ============================================================
# RENDER LOOP
# ============================================================

async def render_loop(state: dict, stop_event: asyncio.Event):

    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    print("Workflow Status")
    print("=" * 50)
    print(state["ssid_conn_line"])
    print(state["conn_line"])
    print(state["prev_line"])
    print(state["fresh_line"])
    print(f"Status: {state['heartbeat']}")
    print(state["action_line"])
    print("")

    TOTAL_LINES = 9

    while not stop_event.is_set():

        update_action_message(state)

        sys.stdout.write(f"\033[{TOTAL_LINES}A")
        sys.stdout.flush()

        print("Workflow Status")
        print("=" * 50)
        print(state["ssid_conn_line"])
        print(state["conn_line"])
        print(state["prev_line"])
        print(state["fresh_line"])
        print(f"Status: {state['heartbeat']}")
        print(state["action_line"])
        print("")

        await asyncio.sleep(UI_REFRESH_INTERVAL)

# ============================================================
# PRESS ENTER
# ============================================================

async def wait_for_enter():
    return await asyncio.to_thread(input, "")

# ============================================================
# ENTRY POINT
# ============================================================

async def run_monitor(
    autosave_previous=True,
    autosave_fresh=True,
    clean_downloads=True
):
    """
    autosave_previous  → automatically save previous captures
    autosave_fresh     → automatically save fresh captures
    clean_downloads    → if True, delete original files after copying
    """

    state = make_state()
    stop_event = asyncio.Event()

    # Detect downloads folder
    download_dir = find_downloads_folder()
    state["download_dir"] = download_dir
    logger.info(f"Using downloads folder: {download_dir}")

    try:
        heartbeat  = asyncio.create_task(heartbeat_worker(state, stop_event))
        ssids      = asyncio.create_task(ssid_worker(state, stop_event))
        connect    = asyncio.create_task(connectivity_worker(state, stop_event))
        captures   = asyncio.create_task(capture_worker(state, stop_event))
        renderer   = asyncio.create_task(render_loop(state, stop_event))

        await wait_for_enter()

    finally:
        # Stop workers
        stop_event.set()
        heartbeat.cancel()
        ssids.cancel()
        connect.cancel()
        captures.cancel()
        renderer.cancel()

        # Restore cursor
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

        print("\nProcessing captured images…\n")

        finalize_capture_export(
            state,
            autosave_previous=autosave_previous,
            autosave_fresh=autosave_fresh,
            clean_downloads=clean_downloads,
        )

        print("\nExiting workflow monitor…\n")
        logger.info("Workflow monitor ended cleanly.")


if __name__ == "__main__":
    asyncio.run(run_monitor())
