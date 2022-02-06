from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from asyncpg import Pool

from src.models import AssetHistory, FinancialAsset


async def test_financial_asset(pool: Pool):
    assets = await FinancialAsset.get_assets(pool)
    assert [asset.symbol for asset in assets] == [
        "EURUSD",
        "USDJPY",
        "GBPUSD",
        "AUDUSD",
        "USDCAD",
    ]
    assert assets[0].symbol == "EURUSD"
    assert assets[0].created_at == assets[0].updated_at
    assert not assets[0].is_deleted


@pytest.mark.usefixtures("clean_table")
async def test_asset_history(pool: Pool):
    assets = await FinancialAsset.get_assets(pool)
    history_after = datetime.utcnow() - timedelta(minutes=30)
    value = Decimal(23.3000011)
    expected_value = Decimal(
        "23.300001"
    )  # Проверим, что в базе корректно настроена точность
    now = datetime.now(timezone.utc)
    asset_id = assets[0].id

    histories = await AssetHistory.get_assets(pool, asset_id, history_after)
    assert histories == []

    history = await AssetHistory.get_last_asset(pool, asset_id)
    assert history is None

    record_id = await AssetHistory.add_asset(pool, assets[0].id, value, now)

    histories = await AssetHistory.get_assets(pool, asset_id, history_after)
    history = await AssetHistory.get_last_asset(pool, asset_id)

    assert len(histories) == 1
    assert histories[0] == history
    assert history.id == record_id
    assert history.asset_id == asset_id
    assert history.value == expected_value
    assert history.created_at == now
