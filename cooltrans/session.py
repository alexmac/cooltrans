from typing import Dict

import aiohttp

from cooltrans.static_resolver import StaticResolver

_shared_sessions: Dict[str, aiohttp.ClientSession] = {}


def get_shared_session(ip: str):
    if ip not in _shared_sessions:
        con = aiohttp.TCPConnector(resolver=StaticResolver(ip))
        _shared_sessions[ip] = aiohttp.ClientSession(connector=con)

    return _shared_sessions[ip]
