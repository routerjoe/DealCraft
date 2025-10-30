import pytest
from httpx import AsyncClient

from mcp.api.main import app


@pytest.mark.asyncio
async def test_partners_endpoints_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.get("/v1/partners/tiers")
        assert r1.status_code == 200
        assert isinstance(r1.json(), list)

        r2 = await ac.post("/v1/partners/sync", json={"sources": [], "dry_run": True})
        assert r2.status_code == 200
        body = r2.json()
        assert "status" in body

        r3 = await ac.get("/v1/partners/export/obsidian")
        assert r3.status_code == 200
        assert "status" in r3.json()
