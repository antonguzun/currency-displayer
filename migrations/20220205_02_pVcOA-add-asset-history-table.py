"""
add asset_history table
"""

from yoyo import step

__depends__ = {"20220205_01_C2CJ5-add-financial-assets-table"}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS asset_history (
            id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            asset_id int references financial_assets(id),
            value decimal(12, 6) NOT NULL,
            created_at timestamp with time zone NOT NULL
        );
        CREATE INDEX IF NOT EXISTS created_at_asset_history ON asset_history (created_at);
        """,
        """
        DROP TABLE IF EXISTS asset_history;
        """,
    ),
]
