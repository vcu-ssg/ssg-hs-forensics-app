import asyncio

async def sleep_and_log(seconds, message):
    print(f"[microscope] {message}")
    await asyncio.sleep(seconds)
