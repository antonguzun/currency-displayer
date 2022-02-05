import os
from subprocess import PIPE, Popen
from urllib.parse import urlparse

import asyncpg
import pytest
from aioresponses import aioresponses
from asyncpg import Pool

from src import settings

database_url = urlparse(settings.DB_URL_TEST)


def _execute_psql(cmd: str):
    """
    Выполняет команду psql
    """
    command = (
        f"psql "
        f"-U {database_url.username} "
        f"-h {database_url.hostname} "
        f"-p {database_url.port or 5432} postgres "
        f"-c '{cmd}'"
    )

    proc = Popen(
        command,
        stdout=PIPE,
        stderr=PIPE,
        env=dict(os.environ, PGPASSWORD=database_url.password),
        shell=True,
    )

    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise Exception("Error during running command %s: \n %s" % (command, stderr))


@pytest.fixture(scope="session", autouse=True)
def db():
    """
    Базовая фикстура для пересоздания тестовой базы данных
    """

    # Удаление базы
    _execute_psql(f"DROP DATABASE IF EXISTS {database_url.path[1:]}")

    # Создание базы
    _execute_psql(f"CREATE DATABASE {database_url.path[1:]}")

    # Применение миграций
    path_to_migrations = os.path.join(settings.BASE_PATH, "migrations")

    command = f"yoyo apply --database '{settings.DB_URL_TEST}' {path_to_migrations} -b"
    proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise Exception("Error during running command %s: \n %s" % (command, stderr))


@pytest.fixture()
async def pool(loop) -> Pool:
    common_settings = {
        "server_settings": {"application_name": "currency_displayer_test"},
        "loop": loop,
    }
    pool = await asyncpg.create_pool(settings.DB_URL_TEST, **common_settings)
    yield pool
    await pool.close()


@pytest.fixture
async def clean_table(loop, pool: Pool):
    await pool.execute("DELETE FROM finansical_assets")


@pytest.fixture
async def app(loop):
    from src.app import app_factory

    return await app_factory()


@pytest.fixture
async def client(loop, app, aiohttp_client):
    if loop.is_running():
        client = await aiohttp_client(app)
        return client
    else:
        return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def mock_aioresponse():
    with aioresponses(passthrough=["http://127.0.0.1",]) as m:
        yield m
