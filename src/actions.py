import asyncio
from collections import Callable
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from pydantic import BaseModel

from src.models import AssetHistory, FinancialAsset
from src.resources import Resources


class WebSocketSchema(BaseModel):
    action: str
    message: dict


class BaseAction:
    def __init__(self, resources: Resources, send_str: Callable):
        self.resources = resources
        self.send_str = send_str

    async def __call__(self, task: WebSocketSchema):
        raise NotImplementedError


def history_to_point(history: AssetHistory) -> dict:
    return {
        "id": history.id,
        "assetName": history.asset_name,
        "assetId": history.asset_id,
        "value": history.value,
        "time": int(history.created_at.timestamp()),
    }


class AssetsAction(BaseAction):
    async def __call__(self, task: WebSocketSchema):
        target_assets = await FinancialAsset.get_assets(self.resources.db_pool)
        message = {
            task.action: [
                {"id": asset.id, "name": asset.symbol} for asset in target_assets
            ]
        }
        resp = WebSocketSchema(action=task.action, message=message).json()
        await self.send_str(resp)


class HistoryAction(BaseAction):
    async def __call__(self, task: WebSocketSchema):
        asset_id = task.message["assetId"]
        history_after = datetime.utcnow() - timedelta(minutes=30)
        histories = await AssetHistory.get_assets(
            self.resources.db_pool, asset_id, history_after
        )
        message = {
            "message": {"points": [history_to_point(history) for history in histories]}
        }
        resp = WebSocketSchema(action="asset_history", message=message).json()
        await self.send_str(resp)


class SubscribeTask(BaseAction):
    async def __call__(self, task: WebSocketSchema):
        while True:
            asset_id = task.message["assetId"]
            await asyncio.sleep(1)
            history = await AssetHistory.get_last_asset(
                self.resources.db_pool, asset_id
            )
            point = history_to_point(history)
            resp = WebSocketSchema(action="point", message=point).json()
            try:
                await self.send_str(resp)
            except ConnectionResetError:
                logger.debug(f"Stop subscribe task for asset {asset_id}")
                return


class ActionRouter(BaseAction):
    """
    Выполняет маршрутизацию сообщений с экшенами и выполяняет его
    Если экшен предполагает создание бэкграунд таски, то отдает ее наружу
    Требует функцию send_str
    """

    def __init__(self, resources: Resources, send_str: Callable):
        super().__init__(resources=resources, send_str=send_str)
        self.run_asset_action = AssetsAction(resources, send_str=send_str)
        self.run_history_action = HistoryAction(resources, send_str=send_str)
        self.subscribe = SubscribeTask(resources, send_str=send_str)
        self.send_str = send_str

    async def __call__(self, msg: str) -> Optional[asyncio.Task]:
        task = WebSocketSchema.parse_raw(msg)

        if task.action == "assets":
            await self.run_asset_action(task)
        elif task.action == "subscribe":
            await self.run_history_action(task)
            return asyncio.create_task(self.subscribe(task))
        else:
            resp = WebSocketSchema(
                action=task.action, message={"error": {"action": "not found"}}
            ).json()
            await self.send_str(resp)
