import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from loguru import logger

from src.clients import ApiError
from src.models import AssetHistory, FinancialAsset
from src.resources import Resources


@dataclass
class CurrencyUpdaterActionError(Exception):
    nested_error: str

    def __str__(self):
        return f"{self.__class__.__name__}. Nested Error: {self.nested_error}"


class CurrencyUpdaterAction:
    def __init__(self, resources: Resources):
        self.resources = resources

    async def get_rates(self) -> dict:
        try:
            return await self.resources.ratejson_fxcm_service.get_rates()
        except (ApiError, asyncio.TimeoutError) as e:
            raise CurrencyUpdaterActionError(nested_error=str(e))

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
        logger.info("currency rates updated")


class CurrencyUpdater:
    action: CurrencyUpdaterAction

    def __init__(self, resources: Resources):
        self.resources = resources
        self.action = CurrencyUpdaterAction(resources)

    async def run(self):
        logger.info(f"start {self.__class__.__name__}")
        target_assets = await FinancialAsset.get_assets(self.resources.db_pool)
        target_symbols = {asset.symbol: asset for asset in target_assets}
        while True:
            logger.debug(f"try to get {target_symbols.keys()}")
            try:
                await self.action(target_symbols)
            except CurrencyUpdaterActionError as e:
                logger.error(e)
            await asyncio.sleep(1)
