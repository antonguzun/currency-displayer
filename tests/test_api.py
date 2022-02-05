async def test_ping(client):
    response = await client.get("/ping")
    assert response.status == 200
    assert await response.json(content_type=None) == {"success": True}
