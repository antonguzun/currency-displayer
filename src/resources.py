from dataclasses import dataclass

import aiohttp
from asyncpg import Pool

from src.dto.current_curencies import CurrentCurrencyRates


@dataclass
class Resources:
    client_session: aiohttp.ClientSession
    current_currency_rates: CurrentCurrencyRates
    db_pool: Pool = None
    ratejson_fxcm_service: str = None  # TODO поменять тип

    async def close(self):
        await self.client_session.close()
        await self.db_pool.close()
