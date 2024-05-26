from typing import Dict, Optional

import aiohttp

from cooltrans.static_resolver import StaticResolver
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor


from aws_xray_sdk.ext.aiohttp.client import aws_xray_trace_config

_shared_sessions_for_ip: Dict[str, aiohttp.ClientSession] = {}

AioHttpClientInstrumentor().instrument()


def get_shared_session_for_ip(ip: str) -> aiohttp.ClientSession:
    if ip not in _shared_sessions_for_ip:
        con = aiohttp.TCPConnector(resolver=StaticResolver(ip))
        tc = aws_xray_trace_config()
        _shared_sessions_for_ip[ip] = aiohttp.ClientSession(
            connector=con, trace_configs=[tc]
        )

    return _shared_sessions_for_ip[ip]


_shared_session: Optional[aiohttp.ClientSession] = None


def get_shared_session() -> aiohttp.ClientSession:
    global _shared_session
    if _shared_session is None:
        tc = aws_xray_trace_config()
        _shared_session = aiohttp.ClientSession(trace_configs=[tc])

    return _shared_session
