# src/ssg_hs_forensics_app/microscope/wifi.py

import asyncio
import sys
import os
from loguru import logger


def running_in_wsl():
    try:
        with open("/proc/version") as f:
            text = f.read().lower()
        is_wsl = "microsoft" in text
        logger.debug(f"WSL detection: {'yes' if is_wsl else 'no'}")
        return is_wsl
    except Exception as e:
        logger.debug(f"WSL detection failed: {e}")
        return False


async def get_current_network():
    """Return the name of the connected WiFi network if available."""
    logger.info("Detecting current WiFi network...")

    # Windows
    if sys.platform.startswith("win"):
        logger.debug("Using Windows WiFi detection via netsh")
        proc = await asyncio.create_subprocess_shell(
            'netsh wlan show interfaces',
            stdout=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()
        text = out.decode(errors="ignore")

        for line in text.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[1].strip()
                logger.info(f"Currently connected to: {ssid}")
                return ssid

        logger.warning("Unable to determine current SSID on Windows.")
        return None

    # macOS
    if sys.platform.startswith("darwin"):
        logger.debug("Using macOS WiFi detection via airport")
        proc = await asyncio.create_subprocess_shell(
            "/System/Library/PrivateFrameworks/Apple80211.framework/"
            "Versions/Current/Resources/airport -I",
            stdout=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()

        for line in out.decode().splitlines():
            if " SSID" in line:
                ssid = line.split(":")[1].strip()
                logger.info(f"Currently connected to: {ssid}")
                return ssid

        logger.warning("Unable to determine current SSID on macOS.")
        return None

    # Linux Desktop
    if sys.platform.startswith("linux") and not running_in_wsl():
        logger.debug("Using Linux WiFi detection via nmcli")
        if os.system("which nmcli > /dev/null 2>&1") == 0:
            proc = await asyncio.create_subprocess_shell(
                "nmcli -t -f ACTIVE,SSID dev wifi",
                stdout=asyncio.subprocess.PIPE
            )
            out, _ = await proc.communicate()

            for line in out.decode().splitlines():
                if line.startswith("yes:"):
                    ssid = line.split(":")[1]
                    logger.info(f"Currently connected to: {ssid}")
                    return ssid

        logger.warning("nmcli not available; cannot detect Linux WiFi SSID.")
        return None

    # WSL or unknown
    logger.info("WiFi detection not supported on this platform.")
    return None


async def connect_to_network(ssid):
    """Connect to a WiFi network or request manual action."""
    logger.info(f"Attempting to connect to: {ssid}")

    # WSL
    if running_in_wsl():
        logger.warning("WSL cannot control WiFi; manual connection required.")
        input(f"Please connect to '{ssid}' manually and press ENTER.")
        return True

    # Windows
    if sys.platform.startswith("win"):
        logger.debug("Running Windows netsh connect command")
        cmd = f'netsh wlan connect name="{ssid}"'
        proc = await asyncio.create_subprocess_shell(cmd)
        await proc.communicate()
        ok = proc.returncode == 0
        logger.info(f"WiFi connect status: {'success' if ok else 'failed'}")
        return ok

    # macOS
    if sys.platform.startswith("darwin"):
        logger.debug("Running macOS networksetup connect command")
        cmd = f'networksetup -setairportnetwork en0 "{ssid}"'
        proc = await asyncio.create_subprocess_shell(cmd)
        await proc.communicate()
        ok = proc.returncode == 0
        logger.info(f"WiFi connect status: {'success' if ok else 'failed'}")
        return ok

    # Linux Desktop
    if sys.platform.startswith("linux"):
        if os.system("which nmcli > /dev/null 2>&1") == 0:
            logger.debug("Running nmcli connect command")
            cmd = f"nmcli dev wifi connect '{ssid}'"
            proc = await asyncio.create_subprocess_shell(cmd)
            await proc.communicate()
            ok = proc.returncode == 0
            logger.info(f"WiFi connect status: {'success' if ok else 'failed'}")
            return ok

    # Fallback
    logger.warning(
        f"No WiFi automation available; please connect manually to '{ssid}'."
    )
    input("Press ENTER when connected…")
    return True
