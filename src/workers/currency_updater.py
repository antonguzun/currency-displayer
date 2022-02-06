import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from loguru import logger

from src.models import AssetHistory, FinancialAsset
from src.resources import Resources
from tests.vars.rates import RATES  # TODO не забыть имплементировать


class CurrencyUpdaterAction:
    def __init__(self, resources: Resources):
        self.resources = resources

    async def get_rates(self) -> dict:
        return await self.resources.ratejson_fxcm_service.get_rates()

    async def __call__(self, symbols_assets_mapping: dict[str, FinancialAsset]):
        rates = await self.get_rates()
        date = datetime.now(timezone.utc)
        for rate in rates:
            if rate["Symbol"] in symbols_assets_mapping.keys():
                value = (Decimal(rate["Bid"]) + Decimal(rate["Ask"])) / 2
                asset = symbols_assets_mapping[rate["Symbol"]]
                await AssetHistory.add_asset(
                    self.resources.db_pool, asset.id, value, date
                )
        logger.info(f"currency rates updated in {date}")


class CurrencyUpdater:
    action: CurrencyUpdaterAction

    def __init__(self, resources: Resources):
        self.resources = resources
        self.action = CurrencyUpdaterAction(resources)

    async def run(self):
        target_assets = await FinancialAsset.get_assets(self.resources.db_pool)
        target_symbols = {asset.symbol: asset for asset in target_assets}
        while True:
            await self.action(target_symbols)
            await asyncio.sleep(1)
