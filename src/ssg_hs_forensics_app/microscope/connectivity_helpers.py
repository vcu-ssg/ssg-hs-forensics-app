import asyncio
import aiohttp

import platform
import subprocess


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


async def open_wifi_settings_screen():
    os_name = platform.system().lower()

    try:
        if os_name == "windows":
            # Windows 10/11 Wi-Fi settings
            # Works on all modern Windows builds
            subprocess.run(["start", "ms-settings:network-wifi"], shell=True)
            return

        elif os_name == "darwin":
            # macOS Wi-Fi Settings (System Settings → Wi-Fi)
            # macOS Ventura and later:
            subprocess.run(["open", "x-apple.systempreferences:com.apple.WiFiSettings"], check=False)

            # Fallback (older macOS):
            subprocess.run(["open", "/System/Library/PreferencePanes/Network.prefPane"], check=False)
            return

        elif os_name == "linux":
            # Linux desktop environments differ widely.
            # Try GNOME first (most common: Ubuntu, Fedora)
            if subprocess.call(["which", "gnome-control-center"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.Popen(["gnome-control-center", "wifi"])
                return

            # KDE
            if subprocess.call(["which", "kcmshell5"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.Popen(["kcmshell5", "networkmanagement"])
                return

            # XFCE (no direct panel → open network manager)
            if subprocess.call(["which", "nm-connection-editor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.Popen(["nm-connection-editor"])
                return

            print("⚠️ Unable to automatically open Wi-Fi settings on this Linux environment.")
            return

        else:
            print(f"⚠️ Unsupported OS: {os_name}")

    except Exception as e:
        print(f"❌ Error opening Wi-Fi settings: {e}")
