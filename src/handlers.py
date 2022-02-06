import asyncio
import json
from datetime import datetime, timedelta
from typing import Callable

import aiohttp
from aiohttp import web
from aiohttp.web_response import Response
from loguru import logger
from pydantic import BaseModel

from src.models import AssetHistory, FinancialAsset
from src.resources import Resources


async def ping(request):
    return Response(status=200, body=json.dumps({"success": True}))


class WebSocketSchema(BaseModel):
    action: str
    message: dict


class BaseAction:
    def __init__(self, resources: Resources):
        self.resources = resources

    async def __call__(self, task: WebSocketSchema, send):
        raise NotImplementedError


class AssetsAction(BaseAction):
    async def __call__(self, task: WebSocketSchema, send):
        target_assets = await FinancialAsset.get_assets(self.resources.db_pool)
        message = {
            task.action: [
                {"id": asset.id, "name": asset.symbol} for asset in target_assets
            ]
        }
        resp = WebSocketSchema(action=task.action, message=message).json()
        await send(resp)


class HistoryAction(BaseAction):
    async def __call__(self, task: WebSocketSchema, send):
        asset_id = task.message["assetId"]
        history_after = datetime.utcnow() - timedelta(minutes=30)
        histories = await AssetHistory.get_assets(
            self.resources.db_pool, asset_id, history_after
        )
        message = {
            "message": {
                "points": [
                    {
                        "id": point.id,
                        "assetName": "FAKE",
                        "assetId": point.asset_id,
                        "value": point.value,
                        "time": int(point.created_at.timestamp()),
                    }
                    for point in histories
                ]
            }
        }
        resp = WebSocketSchema(action="asset_history", message=message).json()
        await send(resp)


class SubscribeTask(BaseAction):
    async def __call__(self, task: WebSocketSchema, send: Callable):
        while True:
            asset_id = task.message["assetId"]
            await asyncio.sleep(1)
            point = await AssetHistory.get_last_asset(
                self.resources.db_pool, asset_id
            )
            message = {
                "id": point.id,
                "assetName": "FAKE",
                "assetId": point.asset_id,
                "value": point.value,
                "time": int(point.created_at.timestamp()),
            }
            resp = WebSocketSchema(action="point", message=message).json()
            try:
                await send(resp)
            except ConnectionResetError:
                logger.debug(f"Stop subscribe task for asset {asset_id}")
                return


class ActionRouter(BaseAction):
    def __init__(self, resources: Resources):
        super().__init__(resources=resources)
        self.run_asset_action = AssetsAction(resources)
        self.run_history_action = HistoryAction(resources)
        self.subscribe = SubscribeTask(resources)

    async def __call__(self, task: WebSocketSchema, send: Callable):
        if task.action == "assets":
            await self.run_asset_action(task, send)
        elif task.action == "subscribe":
            await self.run_history_action(task, send)
            return asyncio.create_task(self.subscribe(task, send))
        else:
            resp = WebSocketSchema(
                action=task.action, message={"error": {"action": "not found"}}
            ).json()
            await send(resp)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    router = ActionRouter(request.app.resources)
    old_task = None
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = WebSocketSchema.parse_raw(msg.data)
            task = await router(data, ws.send_str)
            if old_task:
                logger.debug("Canceling old task")
                old_task.cancel()
            old_task = task
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(f"ws connection closed with exception {ws.exception()}")
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            if old_task:
                logger.debug("Canceling old task")
                old_task.cancel()
    logger.info("websocket connection closed")
    return ws
