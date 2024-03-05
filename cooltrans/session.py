from typing import Dict, Optional

import aiohttp

from cooltrans.static_resolver import StaticResolver

_shared_sessions_for_ip: Dict[str, aiohttp.ClientSession] = {}


def get_shared_session_for_ip(ip: str) -> aiohttp.ClientSession:
    if ip not in _shared_sessions_for_ip:
        con = aiohttp.TCPConnector(resolver=StaticResolver(ip))
        _shared_sessions_for_ip[ip] = aiohttp.ClientSession(connector=con)

    return _shared_sessions_for_ip[ip]


_shared_session: Optional[aiohttp.ClientSession] = None


def get_shared_session() -> aiohttp.ClientSession:
    global _shared_session
    if _shared_session is None:
        _shared_session = aiohttp.ClientSession()

    return _shared_session
