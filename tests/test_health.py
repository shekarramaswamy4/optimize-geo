"""Tests for health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health endpoint returns correct status."""
    response = await client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_readiness_endpoint(client: AsyncClient):
    """Test readiness endpoint returns correct status."""
    response = await client.get("/readiness")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"