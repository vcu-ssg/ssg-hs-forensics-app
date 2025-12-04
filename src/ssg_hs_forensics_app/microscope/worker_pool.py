import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def run_blocking(func, *args, **kwargs):
    """
    Runs a blocking function without freezing the async event loop.
    Useful for file polling, heavy IO, or libraries that aren't async.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor,
        lambda: func(*args, **kwargs)
    )
