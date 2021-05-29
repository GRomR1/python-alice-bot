import sys
import aiohttp
import asyncio


async def bound_fetch(sem, url, session):
    async with sem:
        async with session.get(url) as response:
            await response.release()


async def main(loop, url):
    count = 10000
    tasks = []
    sem = asyncio.Semaphore(count)
    async with aiohttp.ClientSession() as session:
        for i in range(count):
            task = asyncio.ensure_future(bound_fetch(sem, "http://" + url, session))
            tasks.append(task)
        await asyncio.gather(*tasks)
    print('done')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, sys.argv[1]))

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        loop.close()
