import platform
from .tasks.wifi.windows import WindowsWifiAdapter
from .tasks.wifi.linux import LinuxWifiAdapter
from .tasks.wifi.darwin import MacWifiAdapter


def get_wifi_adapter():
    system = platform.system().lower()

    if system == "windows":
        return WindowsWifiAdapter()
    elif system == "linux":
        return LinuxWifiAdapter()
    elif system == "darwin":
        return MacWifiAdapter()
    else:
        raise RuntimeError(f"Unsupported OS: {system}")
