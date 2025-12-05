import platform
import subprocess
import asyncio
import re

IOLIGHT_REGEX = re.compile(r"^iolight\d+$", re.IGNORECASE)


def get_connected_ssid():
    system = platform.system().lower()

    try:
        if system == "windows":
            output = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                text=True, errors="ignore"
            )
            for line in output.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":", 1)[1].strip()
                    return ssid if ssid else None

        elif system == "darwin":
            airport = (
                "/System/Library/PrivateFrameworks/"
                "Apple80211.framework/Versions/Current/Resources/airport"
            )
            output = subprocess.check_output([airport, "-I"], text=True, errors="ignore")
            for line in output.splitlines():
                if " SSID:" in line:
                    ssid = line.split(":", 1)[1].strip()
                    return ssid if ssid else None

        else:  # Linux
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                text=True, errors="ignore"
            )
            for line in output.splitlines():
                if line.startswith("yes:"):
                    ssid = line.split(":", 1)[1]
                    return ssid if ssid else None

    except Exception:
        return None

    return None


async def ssid_worker(state: dict, stop_event: asyncio.Event):
    """
    Updates:
        state["ssid_conn_line"]
        state["is_iolight_ssid"]
    """
    while not stop_event.is_set():

        connected = get_connected_ssid()
        connected_clean = connected.strip() if connected else None
        is_iolight = bool(connected_clean and IOLIGHT_REGEX.match(connected_clean))

        # Store for other workers
        state["is_iolight_ssid"] = is_iolight

        # Row 1 — Connected SSID
        if not connected_clean:
            state["ssid_conn_line"] = "Connected SSID: (none)"
        else:
            tag = "ioLight" if is_iolight else "other"
            icon = "✔" if is_iolight else "✖"
            state["ssid_conn_line"] = (
                f"Connected SSID: {connected_clean} ({tag} {icon})"
            )

        await asyncio.sleep(1.0)
