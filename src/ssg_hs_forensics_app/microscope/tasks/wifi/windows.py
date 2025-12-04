import asyncio
from .base import WifiAdapter


class WindowsWifiAdapter(WifiAdapter):

    async def connect(self, ssid, password=None):
        cmd = f'netsh wlan connect name="{ssid}"'
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        return proc.returncode, out.decode(), err.decode()

    async def current_network(self):
        cmd = "netsh wlan show interfaces"
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()

        for line in out.decode().splitlines():
            if "SSID" in line and "BSSID" not in line:
                return line.split(":", 1)[1].strip()

        return "unknown"

    async def restore(self, ssid):
        return await self.connect(ssid)
