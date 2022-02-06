from decimal import Decimal
from unittest.mock import patch

import pytest

from src.models import AssetHistory, FinancialAsset
from src.workers.currency_updater import CurrencyUpdaterActionPipeline
from tests.vars.rates import CLIENT_RESPONSE


@pytest.mark.usefixtures("clean_table")
@patch("src.clients.RateJsonFXCMClient.get_rates", return_value=CLIENT_RESPONSE)
async def test_updater(client, pool, resources):
    # Для этого запроса не получилось сделать корректный мок,
    #   тк aioresponse в качестве payload может принять только корректный json
    # mock_aioresponse.get(
    #     "https://fake.url/DataDisplayer", payload=RAW_RATES,
    # )
    target_assets = await FinancialAsset.get_assets(pool)
    target_symbols = {asset.symbol: asset for asset in target_assets}

    action = CurrencyUpdaterActionPipeline(resources)
    await action(target_symbols)

    point_count = await pool.fetchval("SELECT count(1) FROM asset_history")
    assert point_count == 5

    asset_value_mapping = {
        target_symbols["EURUSD"].id: Decimal("1.145095"),
        target_symbols["USDJPY"].id: Decimal("115.200000"),
        target_symbols["GBPUSD"].id: Decimal("1.353535"),
        target_symbols["AUDUSD"].id: Decimal("0.707725"),
        target_symbols["USDCAD"].id: Decimal("1.276575"),
    }
    for asset_id, value in asset_value_mapping.items():
        history = await AssetHistory.get_last_asset(pool, asset_id)
        assert history.value == value
