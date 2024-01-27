import asyncio
from typing import Dict, Set

import aiohttp
from yarl import URL


async def get_valid_stream_paths() -> Set[str]:
    valid_paths = set()
    async with aiohttp.ClientSession() as session:
        for i in range(12):
            async with session.get(
                f"https://cwwp2.dot.ca.gov/data/d{i+1}/cctv/cctvStatusD{i+1:0>{2}}.json",
            ) as r:
                body = await r.json()
            for d in body["data"]:
                valid_paths.add(
                    URL(d["cctv"]["imageData"]["streamingVideoURL"]).parent.path
                )

    return valid_paths


async def get_valid_cctv_locations() -> Dict[str, Dict]:
    cctv_locations = dict()
    async with aiohttp.ClientSession() as session:
        for i in [2]:
            async with session.get(
                f"https://cwwp2.dot.ca.gov/data/d{i+1}/cctv/cctvStatusD{i+1:0>{2}}.json",
            ) as r:
                body = await r.json()
            for d in body["data"]:
                cctv = d["cctv"]
                if cctv["inService"] != "true":
                    continue
                try:
                    name = f'{cctv["location"]["district"]} / {cctv["location"]["nearbyPlace"]} / {cctv["location"]["locationName"]}'

                    cctv_locations[name] = {
                        "longitude": cctv["location"]["longitude"],
                        "latitude": cctv["location"]["latitude"],
                        "stream": URL(
                            cctv["imageData"]["streamingVideoURL"]
                        ).parent.path,
                    }
                except Exception:
                    pass

    return cctv_locations


async def main():  # pragma: nocover
    with open("testout", "wt+") as f:
        f.write(str(await get_valid_cctv_locations()))


if __name__ == "__main__":  # pragma: nocover
    asyncio.run(main())
