"""
This script pulls all 2142 every corporate score pages and stores their .html
in the pages directory.
"""

from typing import List, Coroutine
import asyncio
import aiohttp
from aiohttp import ClientResponse
import requests
from bs4 import BeautifulSoup
from time import sleep


async def get_and_save_css() -> None:
    URL = "https://api.2ndvote.com/css/wp.css?ver=2.2.1"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            css = await resp.text()

    with open(f'pages/wp.css', 'w') as f:
        f.write(css)


async def get_and_save_js() -> None:
    URL = 'https://api.2ndvote.com/js/wp.min.js?ver=2.2.1'
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            js = await resp.text()

    with open(f'pages/wp.min.js', 'w') as f:
        f.write(js)


async def get_and_save(url_path: str) -> None:
    BASE="https://www.2ndvote.com/"

    company_name= url_path.split('/')[2]

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE}{url_path}") as resp:
                    html = await resp.text()
            break
        except asyncio.CancelledError:
            # Handle cancellation by allowing it to propagate
            raise
        except Exception as e:
            # Handle other exceptions if needed
            print(f"Error fetching {url_path}: {e}")
            await asyncio.sleep(2)  # Wait before retrying

    with open(f'pages/{company_name}.html', 'w', encoding='utf-8') as f:
        f.write(html)


async def get_and_save_html() -> None:

    # Note there are only 2142 corporate rating pages. 2500 will get all of these
    API_ENDPOINT = "https://api.2ndvote.com/organization/wp_grid?limit=2500&offset=0"
    divs = '\n'.join(requests.get(API_ENDPOINT).json()['payload'])
    soup = BeautifulSoup(divs, 'html.parser')

    paths: List[str] = []
    for div in soup.find_all(class_='organization-score-grid'):
        paths.append(div.a.get('href'))
    print(f"Found {len(paths)} paths to gather")

    coros: List[Coroutine] = []
    for path in paths:
        coros.append(get_and_save(path))

    # Getting HTTP errors. Going to back off on rate.
    STEP = 10
    progress = 0
    while coros:
        subset = coros[0:STEP]
        for _ in range(len(subset)):
            coros.pop(0)
        await asyncio.gather(*subset)
        progress += STEP
        print(f"Progress: {progress} / {len(paths)}")


async def main():
    await get_and_save_css()
    await get_and_save_js()
    await get_and_save_html()
    print("Done.")


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())