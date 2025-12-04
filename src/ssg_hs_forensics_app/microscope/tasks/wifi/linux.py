import asyncio
from .base import WifiAdapter

class LinuxWifiAdapter(WifiAdapter):

    async def connect(self, ssid, password=None):
        cmd = f'nmcli device wifi connect "{ssid}"'
        if password:
            cmd += f' password "{password}"'
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        return await proc.communicate()

    async def current_network(self):
        cmd = 'nmcli -t -f active,ssid dev wifi | egrep "^yes"'
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()
        return out.decode().strip().split(":")[-1]

    async def restore(self, ssid):
        return await self.connect(ssid)
