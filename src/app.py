import aiohttp
import asyncpg
from aiohttp import web

from src import settings
from src.handlers import ping
from src.resources import Resources


async def create_pool(app) -> asyncpg.Pool:
    common_settings = {
        "server_settings": {"application_name": "currency_displayer"},
    }
    return await asyncpg.create_pool(
        settings.DB_URL, min_size=5, max_size=10, **common_settings
    )


async def setup_app_objects(app):
    session = aiohttp.ClientSession()
    pool = await create_pool(app)
    app.resources = Resources(
        db_pool=pool,
        client_session=session,
        ratejson_fxcm_service=None,  # TODO fix
        current_currency_rates=None,
    )


async def cleanup_app_objects(app):
    await app.resources.close()


def register_routers(app):
    app.router.add_get("/ping", ping)


async def app_factory():
    app = web.Application()

    app.on_startup.append(setup_app_objects)
    app.on_cleanup.append(cleanup_app_objects)

    register_routers(app)
    return app


if __name__ == "__main__":
    web.run_app(app_factory(), port=8000)
