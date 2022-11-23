"""
  Simple wrapper for asyncio.sleep
  (mosly needed to replace it with testing double during unit testing)
"""
import asyncio


class Sleeper:

  async def sleep(self, seconds: float) -> None:
    await asyncio.sleep(seconds)
