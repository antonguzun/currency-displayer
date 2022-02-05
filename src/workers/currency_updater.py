import asyncio

from loguru import logger

from src.dto.current_curencies import CurrentCurrencyRates
from src.resources import Resources
from tests.vars.rates import RATES  # TODO не забыть имплементировать


class CurrencyUpdaterAction:
    def __init__(self, resources: Resources):
        self.resources = resources

    async def __call__(self):
        self.resources.current_currency_rates = CurrentCurrencyRates(
            rates=RATES["Rates"]
        )
        logger.info("currency rates updated")


class CurrencyUpdater:
    action: CurrencyUpdaterAction

    def __init__(self, resources: Resources):
        self.action = CurrencyUpdaterAction(resources)

    async def run(self):
        while True:
            await self.action()
            await asyncio.sleep(1)
