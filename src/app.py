import asyncio
import socket
import sys

import aiohttp
import asyncpg
from aiohttp import web

from src import settings
from src.clients import RateJsonFXCMClient
from src.handlers import ping
from src.resources import Resources
from src.workers.currency_updater import CurrencyUpdater


async def create_pool(app) -> asyncpg.Pool:
    common_settings = {
        "server_settings": {"application_name": "currency_displayer"},
    }
    try:
        return await asyncpg.create_pool(
            settings.DB_URL, min_size=5, max_size=10, **common_settings
        )
    except socket.gaierror as e:
        app.logger.error(f"Error during execute db pool. {e}")
        sys.exit(1)


async def setup_app_objects(app):
    session = aiohttp.ClientSession()
    pool = await create_pool(app)

    app.resources = Resources(
        db_pool=pool,
        client_session=session,
        ratejson_fxcm_service=RateJsonFXCMClient(
            settings.RATEJSON_FXCM_SERVICE, session
        ),
    )


async def cleanup_app_objects(app):
    await app.resources.close()


def register_routers(app):
    app.router.add_get("/ping", ping)


async def start_background_tasks(app):
    updater = CurrencyUpdater(app.resources)
    app["currency_updater"] = asyncio.create_task(updater.run())


async def cleanup_background_tasks(app):
    app["currency_updater"].cancel()
    await app["currency_updater"]


async def app_factory(test: bool = False):
    from loguru import logger

    app = web.Application(logger=logger)

    app.on_startup.append(setup_app_objects)
    app.on_cleanup.append(cleanup_app_objects)
    if not test:
        app.on_startup.append(start_background_tasks)
        app.on_cleanup.append(cleanup_background_tasks)

    register_routers(app)
    return app


if __name__ == "__main__":
    web.run_app(app_factory(), port=8000)
