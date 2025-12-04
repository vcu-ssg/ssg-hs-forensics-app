import asyncio
from .platform import get_wifi_adapter
from .session import Session
from .tasks import browser, capture, pull


async def run_full_session():
    """
    Orchestrates the entire microscope workflow:
    1. Detect original Wi-Fi
    2. Connect to microscope network
    3. Verify connectivity
    4. Launch microscope UI
    5. Wait for new images
    6. Pull new images into project
    7. Restore original network
    """
    wifi = get_wifi_adapter()
    session = Session.start_new()

    try:
        # STEP 0 — record original network
        original = await wifi.current_network()
        session.original_network = original
        session.log_step("original_network", original)

        # STEP 1 — connect to microscope
        rc, out, err = await wifi.connect("iolight")
        session.log_step("connect_to_microscope", rc, out, err)
        if rc != 0:
            raise RuntimeError("Failed to connect to microscope Wi-Fi")

        # STEP 2 — verify microscope reachable
        ok = await capture.verify_microscope()
        session.log_step("verify_microscope", ok)
        if not ok:
            raise RuntimeError("Microscope not reachable")

        # STEP 3 — launch UI
        await browser.launch_ui()
        session.log_step("launch_ui")

        # STEP 4 — wait for new images
        images = await capture.wait_for_images(timeout=300)
        session.log_step("capture_images", images)

        # STEP 5 — pull them
        pulled = await pull.pull_images(images)
        session.log_step("pull_images", pulled)

        session.complete()
        return session

    except Exception as exc:
        session.fail(exc)
        raise

    finally:
        # STEP 6 — restore Wi-Fi
        await wifi.restore(session.original_network)
        session.log_step("restore_network", session.original_network)
