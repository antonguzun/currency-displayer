import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Optional

from aiohttp import ClientSession
from loguru import logger


@dataclass
class ApiError(Exception):
    status: int
    content: Optional[str]
    error: Optional[str]


def sanitized_loads(s):
    s = (
        s[8:-5]
        .replace("\t", "")
        .replace("\n", "")
        .replace(",}", "}")
        .replace(",]", "]")
        .replace("\\", "")
    )
    return json.loads(s)


class RateJsonFXCMClient:
    url: str
    api_key: str
    session: ClientSession

    def __init__(self, settings: dict, session: ClientSession):
        self.url = settings["URL"]
        self.client_session = session

    async def get_rates(self) -> dict:
        url = f"{self.url}/DataDisplayer/"
        async with self.client_session.get(url, ssl=False) as resp:
            if resp.status != 200:
                try:
                    content = await resp.text()
                except Exception as e:
                    logger.exception(e)
                    content = None
                raise ApiError(status=resp.status, content=content, error=None)
            try:
                data = await resp.json(loads=sanitized_loads)
                return data["Rates"]
            except JSONDecodeError as e:
                content = await resp.text()
                raise ApiError(
                    status=resp.status, content=content, error=f"wrong json: {e}"
                )
            except KeyError:
                raise ApiError(
                    status=resp.status,
                    content=json.dumps(data),
                    error=f"resp json has not key 'Rates'",
                )
