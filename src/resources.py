from dataclasses import dataclass

import aiohttp
from asyncpg import Pool

from src.clients import RateJsonFXCMClient


@dataclass
class Resources:
    client_session: aiohttp.ClientSession
    db_pool: Pool = None
    ratejson_fxcm_service: RateJsonFXCMClient = None

    async def close(self):
        await self.client_session.close()
        await self.db_pool.close()
