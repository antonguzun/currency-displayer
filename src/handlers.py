import json

from aiohttp.web_response import Response


async def ping(request):
    return Response(status=200, body=json.dumps({"success": True}))
