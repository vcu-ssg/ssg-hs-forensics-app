import asyncio
from .base import WifiAdapter

class MacWifiAdapter(WifiAdapter):

    async def connect(self, ssid, password=None):
        cmd = f'networksetup -setairportnetwork en0 "{ssid}" "{password or ""}"'
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        return await proc.communicate()

    async def current_network(self):
        cmd = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I'
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()

        for line in out.decode().splitlines():
            if " SSID" in line:
                return line.split(":")[1].strip()

        return "unknown"

    async def restore(self, ssid):
        return await self.connect(ssid)
