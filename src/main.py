import asyncio
import json
import re
from datetime import datetime

import aiohttp
import motor.motor_asyncio
import yarl
from bs4 import BeautifulSoup
from pymongo.errors import DuplicateKeyError

match_article = re.compile(r"/\w+/\w+/[0-9]{8}/.+").match

rules = [
    lambda url: re.compile(r"^/.*").match(url),
    lambda url: not re.compile(r"\.(jpg|gif|png)$").match(url),
    lambda url: not re.compile(r".*/(files|video|taxonomy|img)/.*").match(url),
]

color = "\x1B[{}".format
blue = color("94m")
red = color("31m")
green = color("32m")

yellow = color("93m")
reset = color("0m")


async def put(fg=blue, **kwargs):
    print(fg, json.dumps(kwargs), reset, flush=True)


async def url_match(url):
    return bool(all((rule(url) for rule in rules)))


def get_collection():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        "mongodb://mongodb:27017", ssl=False
    )
    return client.lostiempos.responses


async def find_response(session, url, follow=False):
    responses = get_collection()
    record = await responses.find_one({"url": url})

    if record:
        return record["content"]

    content = await fetch(session, url)

    if content is None:
        return

    try:
        await responses.insert_one(
            {
                "url": url,
                "content": content,
                "created_at": datetime.now(),
                "follow": follow,
                "is_article": match_article(url),
            }
        )
    except DuplicateKeyError:
        return

    return content


async def response_exists(url) -> bool:
    responses = get_collection()
    result = await responses.find_one({"url": url})
    return not (result is None)


async def fetch(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()


founded_links = set()


async def find_links(html, fg):
    soup = BeautifulSoup(html, "html5lib")

    for link in soup.select("a"):
        if await url_match(link.attrs["href"]):
            if link.attrs["href"] in founded_links:
                continue

            url = yarl.URL(f'https://www.lostiempos.com{link.attrs["href"]}')

            if url.fragment or url.query:
                continue

            if await response_exists(str(url)):
                continue

            await put(fg, url=url.path, new=True)

            founded_links.add(url.path)

            yield url


crawled = set()


async def crawl(url, follow=False, depth=1, fg=blue):
    if url in crawled:
        return

    if not follow:
        return

    await put(fg, crawl=url, follow=follow, depth=depth)

    async with aiohttp.ClientSession() as session:
        html = await find_response(session, url, follow=follow)

        if html is None:
            return

        crawled.add(url)

        async for link in find_links(html, fg):
            await crawl(str(link), follow=depth <= 3, depth=depth + 1, fg=fg)


async def main():
    await asyncio.wait([
            crawl("https://www.lostiempos.com", follow=True, fg=blue),
            crawl("https://www.lostiempos.com/actualidad", follow=True, fg=red),
            crawl("https://www.lostiempos.com/ultimas-noticias", follow=True, fg=green),

    ])


if __name__ == "__main__":
    asyncio.run(main())
