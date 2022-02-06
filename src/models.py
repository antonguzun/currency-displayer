from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from asyncpg import Pool
from pydantic import BaseModel

from src import settings


class FinancialAsset(BaseModel):
    id: int
    symbol: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    _get_query = """
        SELECT id, symbol, created_at, updated_at, is_deleted 
        FROM financial_assets 
        WHERE is_deleted = $1
    """

    @classmethod
    async def get_assets(
        cls, pool: Pool, is_deleted: bool = False
    ) -> List["FinancialAsset"]:
        results = await pool.fetch(
            cls._get_query, is_deleted, timeout=settings.DB_QUERY_TIMEOUT
        )
        if results:
            return [cls(**result) for result in results]
        return []


class AssetHistory(BaseModel):
    id: int
    asset_id: int
    asset_name: str
    value: Decimal
    created_at: datetime

    _get_assets_after_query = """
        SELECT ah.id, asset_id, fa.symbol as asset_name, value, ah.created_at 
        FROM asset_history ah
        LEFT JOIN financial_assets fa ON asset_id = fa.id
        WHERE asset_id = $1
        AND ah.created_at > $2
        ORDER BY ah.created_at ASC
    """

    _get_last_assets_query = """
        SELECT ah.id, asset_id, fa.symbol as asset_name, value, ah.created_at 
        FROM asset_history ah
        LEFT JOIN financial_assets fa ON asset_id = fa.id
        WHERE asset_id = $1
        ORDER BY ah.created_at DESC
        LIMIT 1
    """

    _insert_asset = """
        INSERT INTO asset_history (asset_id, value, created_at)
        VALUES ($1, $2, $3)
        RETURNING id
    """

    @classmethod
    async def get_assets(
        cls, pool: Pool, asset_id: int, created_after: datetime
    ) -> List["AssetHistory"]:
        results = await pool.fetch(
            cls._get_assets_after_query,
            asset_id,
            created_after,
            timeout=settings.DB_QUERY_TIMEOUT,
        )
        if results:
            return [cls(**result) for result in results]
        return []

    @classmethod
    async def get_last_asset(
        cls, pool: Pool, asset_id: int
    ) -> Optional["AssetHistory"]:
        result = await pool.fetchrow(
            cls._get_last_assets_query, asset_id, timeout=settings.DB_QUERY_TIMEOUT
        )
        if result:
            return cls(**result)
        return None

    @classmethod
    async def add_asset(
        cls, pool: Pool, asset_id: int, value: Decimal, created_at: datetime
    ) -> int:
        return await pool.fetchval(
            cls._insert_asset,
            asset_id,
            value,
            created_at,
            timeout=settings.DB_QUERY_TIMEOUT,
        )
