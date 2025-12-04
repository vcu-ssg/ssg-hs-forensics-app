from abc import ABC, abstractmethod


class WifiAdapter(ABC):

    @abstractmethod
    async def connect(self, ssid: str, password: str | None = None):
        ...

    @abstractmethod
    async def restore(self, ssid: str):
        ...

    @abstractmethod
    async def current_network(self) -> str:
        ...
