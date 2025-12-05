import asyncio
import aiohttp

MICROSCOPE_URL = "http://192.168.1.1/"


async def check_microscope_online(timeout=2.0) -> bool:
    """Returns True if the microscope responds to an HTTP GET."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(MICROSCOPE_URL, timeout=timeout) as resp:
                return resp.status == 200
    except Exception:
        return False


async def connectivity_worker(state: dict, stop_event: asyncio.Event):
    """
    Updates:
        state["conn_line"]
        state["action_line"]
    But coordination logic is handled by workflow_monitor.
    """
    while not stop_event.is_set():

        online = await check_microscope_online()
        state["microscope_online"] = online  # store raw state

        if online:
            state["conn_line"] = "Microscope connected: ✔"
        else:
            state["conn_line"] = "Microscope connected: ✖"

        await asyncio.sleep(1.0)
