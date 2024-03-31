from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
import tempfile
from functools import partial
from typing import List, Optional


from aiohttp.typedefs import Handler, Middleware
from aiohttp.web import (
    HTTPBadRequest,
    Request,
    Response,
    StreamResponse,
    json_response,
    middleware,
)
from alxhttp.file import get_file
from alxhttp.headers import content_security_policy, permissions_policy
from alxhttp.middleware import default_middleware
from alxhttp.server import Server
from alxhttp.xray import init_xray
from yarl import URL

from cooltrans.data.cctv import cctv_locations
from cooltrans.data.ips import useable_ips
from cooltrans.data.ndot_cctv import ndot_cctv_locations
from cooltrans.data.streams import valid_paths
from cooltrans.data.urls import ndot_baseurl
from cooltrans.multi_get import multi_get
from cooltrans.session import get_shared_session

stream_file_pattern = re.compile(
    r"/((D\d+)|(live))/[\w-]+\.stream/(playlist\.m3u8|chunklist_w\d+\.m3u8|media_w\d+_\d+\.ts)"
)

ndot_file_pattern = re.compile(
    r"/renoxcd(0[0-9])/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}_hspflirxcd(0[0-9])_public\.stream/(playlist\.m3u8|chunklist_w\d+\.m3u8|media_w\d+_\d+\.ts)"
)

origin = URL(os.environ.get("OVERRIDE_ORIGIN", "https://0xcafe.tech/"))


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


async def ndot_proxy(s: CooltransServer, req: Request) -> StreamResponse:
    loc = URL.build(path=req.match_info["loc"])

    if not ndot_file_pattern.match(f"/{loc.path}"):
        return HTTPBadRequest(text="invalid path")

    async with get_shared_session().get(ndot_baseurl / loc.path) as r:
        if r.status == 200:
            body = await r.read()
            content_type = r.headers["content-type"]
        else:
            return HTTPBadRequest(text="invalid file")

    return Response(
        body=body,
        status=200,
        headers={
            "cache-control": "public, max-age=10, stale-while-revalidate=60",
            "content-type": content_type,
        },
    )


async def _thumbnail_from_stream(url: URL) -> StreamResponse:
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".jpeg") as tf:
        process = await asyncio.create_subprocess_exec(
            *[
                "ffmpeg",
                "-y",
                "-i",
                str(url),
                "-vframes",
                "1",
                tf.name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        await process.communicate()

        body = tf.read()

    return Response(
        body=body,
        status=200,
        headers={
            "cache-control": "public, max-age=60, stale-while-revalidate=600",
            "content-type": "image/jpeg",
        },
    )


async def caltrans_thumbnail(s: CooltransServer, req: Request) -> StreamResponse:
    loc = URL.build(path=req.match_info["loc"])

    if f"/{loc.parent}" not in valid_paths:
        return HTTPBadRequest(text="invalid path")

    if not stream_file_pattern.match(f"/{loc.path}"):
        return HTTPBadRequest(text="invalid path")

    if not loc.path.endswith("playlist.m3u8"):
        return HTTPBadRequest(text="invalid path")

    return await _thumbnail_from_stream(
        origin / f"api/cooltrans/proxy/caltrans/{loc.path}"
    )


async def ndot_thumbnail(s: CooltransServer, req: Request) -> StreamResponse:
    loc = URL.build(path=req.match_info["loc"])

    if not ndot_file_pattern.match(f"/{loc.path}"):
        return HTTPBadRequest(text="invalid path")

    if not loc.path.endswith("playlist.m3u8"):
        return HTTPBadRequest(text="invalid path")

    return await _thumbnail_from_stream(origin / f"api/cooltrans/proxy/ndot/{loc.path}")


async def caltrans_cctv_locations(s: CooltransServer, req: Request) -> StreamResponse:
    return json_response(
        {
            "locations": {
                **cctv_locations,
                **ndot_cctv_locations,
            }
        }
    )


@middleware
async def security_headers(request: Request, handler: Handler):
    resp = await handler(request)

    resp.headers["content-security-policy"] = content_security_policy(
        default_src=["self"],
        script_src=[
            "self",
            "https://unpkg.com",
            "unsafe-inline",
        ],
        style_src=["self", "https://unpkg.com", "unsafe-inline"],
        font_src=["self", "data:"],
        media_src=["self"],
        object_src=["none"],
        img_src=[
            "self",
            "data:",
            "https://unpkg.com",
            "https://tile.openstreetmap.org",
        ],
        worker_src=["blob:"],
    )

    resp.headers["permissions-policy"] = permissions_policy(
        autoplay=["self"],
        fullscreen=["self"],
    )

    # resp.headers["Access-Control-Allow-Origin"] = "http://localhost:8080"

    return resp


class CooltransServer(Server):
    def __init__(self, middlewares: Optional[List[Middleware]] = None):
        super().__init__(middlewares=middlewares)

        self.app.router.add_get("/", get_file("static/index.html"))
        self.app.router.add_get("/leaflet.js", get_file("static/leaflet.js"))
        self.app.router.add_get("/leaflet.css", get_file("static/leaflet.css"))

        self.app.router.add_get(
            r"/api/cooltrans/proxy/caltrans/{loc:.+}", partial(caltrans_proxy, self)
        )
        self.app.router.add_get(
            r"/api/cooltrans/thumbnail/caltrans/{loc:.+}",
            partial(caltrans_thumbnail, self),
        )

        self.app.router.add_get(
            r"/api/cooltrans/proxy/ndot/{loc:.+}", partial(ndot_proxy, self)
        )
        self.app.router.add_get(
            r"/api/cooltrans/thumbnail/ndot/{loc:.+}",
            partial(ndot_thumbnail, self),
        )

        self.app.router.add_get(
            r"/api/cooltrans/cctv/locations", partial(caltrans_cctv_locations, self)
        )


async def main():  # pragma: nocover
    asyncio.get_running_loop().set_debug(True)
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger()

    xray_enabled = await init_xray(log=log, service_name="cooltrans")

    middlewares = default_middleware(include_xray=xray_enabled)
    middlewares.append(security_headers)

    s = CooltransServer(middlewares=middlewares)
    log.info(f"server origin: {origin}")
    await s.run_app(log, host="0.0.0.0", port=8081)


if __name__ == "__main__":  # pragma: nocover
    asyncio.run(main())
