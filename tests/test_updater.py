from decimal import Decimal

import pytest

from src.models import AssetHistory, FinancialAsset
from src.workers.currency_updater import CurrencyUpdaterAction
from tests.vars.rates import RAW_RATES


@pytest.mark.usefixtures("clean_table")
async def test_updater(client, mock_aioresponse, pool, app):
    mock_aioresponse.get(
        "https://fake.url/DataDisplayer/", payload=RAW_RATES,
    )
    target_assets = await FinancialAsset.get_assets(pool)
    target_symbols = {asset.symbol: asset for asset in target_assets}

    action = CurrencyUpdaterAction(app.resources)
    await action(target_symbols)

    point_count = await pool.fetchval("SELECT count(1) FROM asset_history")
    assert point_count == 5

    asset_value_mapping = {
        target_symbols["EURUSD"].id: Decimal("1.129575"),
        target_symbols["USDJPY"].id: Decimal("114.510000"),
        target_symbols["GBPUSD"].id: Decimal("1.355665"),
        target_symbols["AUDUSD"].id: Decimal("0.712380"),
        target_symbols["USDCAD"].id: Decimal("1.268140"),
    }
    for asset_id, value in asset_value_mapping.items():
        history = await AssetHistory.get_last_asset(pool, asset_id)
        assert history.value == value
