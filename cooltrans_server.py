from __future__ import annotations

import asyncio
import logging
import re
from functools import partial
from typing import List, Optional

from aiohttp.typedefs import Handler, Middleware
from aiohttp.web import (
    FileResponse,
    HTTPBadRequest,
    Request,
    Response,
    StreamResponse,
    json_response,
    middleware,
)
from alxhttp.middleware import default_middleware
from alxhttp.server import Server
from yarl import URL

from cooltrans.data.cctv import cctv_locations
from cooltrans.data.ips import useable_ips
from cooltrans.data.streams import valid_paths
from cooltrans.multi_get import multi_get

stream_file_pattern = re.compile(
    r"/((D\d+)|(live))/[\w-]+\.stream/(playlist\.m3u8|chunklist_w\d+\.m3u8|media_w\d+_\d+\.ts)"
)


async def caltrans_proxy(s: CooltransServer, req: Request) -> StreamResponse:
    loc = URL.build(path=req.match_info["loc"])

    if f"/{loc.parent}" not in valid_paths:
        return HTTPBadRequest(text="invalid path")

    if not stream_file_pattern.match(f"/{loc.path}"):
        return HTTPBadRequest(text="invalid path")

    body, content_type = await multi_get(useable_ips, loc.path, s.app.logger)
    return Response(
        body=body,
        status=200,
        headers={
            "cache-control": "public, max-age=10, stale-while-revalidate=60",
            "content-type": content_type,
        },
    )


async def caltrans_cctv_locations(s: CooltransServer, req: Request) -> StreamResponse:
    return json_response({"locations": cctv_locations})


def get_file(fn: str):
    async def handler(_):
        return FileResponse(fn)

    return handler


@middleware
async def security_headers(request: Request, handler: Handler):
    resp = await handler(request)
    resp.headers[
        "content-security-policy"
    ] = "default-src 'self'; script-src 'self' https://unpkg.com 'sha256-7TblKF+IjWKavJTjUFzFm8Su2HRYXIttPzbcPZBCTwY='; media-src 'self'; worker-src blob: ; style-src 'self' https://unpkg.com 'unsafe-inline'; font-src 'self' data: ; img-src 'self' data: https://unpkg.com https://tile.openstreetmap.org ;"
    resp.headers[
        "permissions-policy"
    ] = "accelerometer=(), autoplay=(self), camera=(), fullscreen=(self), geolocation=(), gyroscope=(), interest-cohort=(), magnetometer=(), microphone=(), payment=(), sync-xhr=()"
    resp.headers["Access-Control-Allow-Origin"] = "http://localhost:8080"

    return resp


class CooltransServer(Server):
    def __init__(self, middlewares: Optional[List[Middleware]] = None):
        super().__init__(middlewares=middlewares)

        self.app.router.add_get("/", get_file("static/index.html"))
        self.app.router.add_get("/leaflet.js", get_file("static/leaflet.js"))
        self.app.router.add_get("/leaflet.css", get_file("static/leaflet.css"))

        self.app.router.add_get(
            r"/api/cooltrans/proxy/{loc:.+}", partial(caltrans_proxy, self)
        )

        self.app.router.add_get(
            r"/api/cooltrans/cctv/locations", partial(caltrans_cctv_locations, self)
        )


async def main():  # pragma: nocover
    asyncio.get_running_loop().set_debug(True)
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger()
    middlewares = default_middleware()
    middlewares.append(security_headers)
    s = CooltransServer(middlewares=middlewares)
    await s.run_app(log, host="0.0.0.0", port=8081)


if __name__ == "__main__":  # pragma: nocover
    asyncio.run(main())
