import socket
from typing import Any, Dict, List

from aiohttp.abc import AbstractResolver


class StaticResolver(AbstractResolver):
    def __init__(self, ip: str):
        super().__init__()
        self._static_ip: str = ip

    async def resolve(
        self, hostname: str, port: int = 0, family: int = socket.AF_INET
    ) -> List[Dict[str, Any]]:
        return [
            {
                "hostname": hostname,
                "host": self._static_ip,
                "port": port,
                "family": family,
                "proto": socket.IPPROTO_TCP,
                "flags": socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
            }
        ]

    async def close(self) -> None:
        pass
