from __future__ import annotations

import asyncio
import logging
from typing import List, Tuple

from aiohttp.web import HTTPTooManyRequests
from tenacity import retry, wait_random_exponential

from cooltrans.data.urls import caltrans_wzmedia_baseurl
from cooltrans.session import get_shared_session_for_ip


async def consume_gathered_tasks(done, pending):
    for t in pending:
        t.cancel()
    for t in pending:
        try:
            await t
        except asyncio.CancelledError:
            pass  # Task cancellation should not be logged as an error.
        except Exception:
            pass

    for t in done:
        try:
            t.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be logged as an error.
        except Exception:
            pass


@retry(wait=wait_random_exponential(multiplier=1, max=5))
async def multi_get(
    useable_ips: List[str], loc: str, log: logging.Logger
) -> Tuple[bytes, str]:
    result = {}
    success = asyncio.Event()

    async def _get(loc: str, ip: str):
        try:
            session = get_shared_session_for_ip(ip)
            async with session.get(caltrans_wzmedia_baseurl / loc) as r:
                if r.status == 200:
                    body = await r.read()
                    log.info({"message": f"got {ip} {loc} ..."})
                    if "body" not in result:
                        result["body"] = body
                        result["content-type"] = r.headers.get("content-type")
                        success.set()
                    return
                else:
                    log.warning({"message": f"failed (http:{r.status}) {ip} {loc} ..."})
                    raise ValueError()
        except asyncio.CancelledError:
            log.debug({"message": f"cancelled {ip} {loc} ..."})
            raise

    done, pending = await asyncio.wait(
        [asyncio.create_task(_get(loc, ip)) for ip in useable_ips],
        return_when=asyncio.FIRST_COMPLETED,
    )

    try:
        while True:
            if success.is_set():
                return (result["body"], result["content-type"])

            if pending:
                newly_done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for t in newly_done:
                    done.add(t)
            else:
                log.error({"message": f"complete failure {loc} ..."})
                raise HTTPTooManyRequests()
    finally:
        await consume_gathered_tasks(done, pending)
