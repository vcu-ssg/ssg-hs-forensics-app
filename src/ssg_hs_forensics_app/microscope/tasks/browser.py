import webbrowser
from ..worker_pool import run_blocking

async def launch_ui():
    """
    Opens the iOLight local web interface in user's browser.
    """
    url = "http://192.168.1.1"  # typical iolight local address
    await run_blocking(webbrowser.open, url)
    return True
