import json

import aiohttp
from aiohttp import web
from aiohttp.web_response import Response
from loguru import logger

from src.actions import ActionRouter


async def ping(request):
    return Response(status=200, body=json.dumps({"success": True}))


async def websocket_handler(request):
    """
    Контроллер перенаправляет сообщение в маршрутизатор и следит за тем,
        чтобы не было более одной бекграунд таски
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    send_str_func = ws.send_str
    router = ActionRouter(request.app.resources, send_str_func)

    old_task = None
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            new_task = await router(msg.data)
            if new_task:
                if old_task:
                    logger.debug("Canceling old task")
                    old_task.cancel()
                old_task = new_task
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(f"ws connection closed with exception {ws.exception()}")
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            if old_task:
                logger.debug("Canceling old task")
                old_task.cancel()

    logger.info("websocket connection closed")
    return ws
