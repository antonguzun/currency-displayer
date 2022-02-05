import json
from datetime import datetime

import pytest

from src.resources import Resources
from src.workers.currency_updater import CurrencyUpdaterAction
from tests.vars.rates import RATES


async def test_updater(client, mock_aioresponse, pool):
    resources = Resources(
        current_currency_rates=None, db_pool=pool, client_session="fake"
    )
    action = CurrencyUpdaterAction(resources)
    await action()
    assert resources.current_currency_rates.rates == RATES["Rates"]
    assert resources.current_currency_rates.created_at is not None
