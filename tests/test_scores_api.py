from security import create_access_token

import pytest


def auth_headers() -> dict[str, str]:
    token = create_access_token("game-server")
    return {"Authorization": f"Bearer {token}"}


pytestmark = pytest.mark.anyio


async def test_add_score_requires_jwt(client):
    response = await client.post("/scores", json={"player_name": "Alex", "score": 100})
    assert response.status_code == 401


async def test_login_returns_token(client):
    response = await client.post(
        "/token",
        data={"username": "GameServer", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


async def test_login_rejects_invalid_credentials(client):
    response = await client.post(
        "/token",
        data={"username": "wrong", "password": "creds"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401


async def test_add_score_rejects_negative_score(client):
    response = await client.post(
        "/scores",
        json={"player_name": "Alex", "score": -10},
        headers=auth_headers(),
    )
    assert response.status_code == 422


async def test_add_score_rejects_invalid_player_name(client):
    response = await client.post(
        "/scores",
        json={"player_name": "A!ex", "score": 120},
        headers=auth_headers(),
    )
    assert response.status_code == 422


async def test_add_score_with_valid_jwt(client):
    response = await client.post(
        "/scores",
        json={"player_name": "Alex", "score": 120},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["player_name"] == "Alex"
    assert payload["score"] == 120


async def test_player_history_pagination(client):
    for score in [100, 110, 120, 130, 140]:
        await client.post(
            "/scores",
            json={"player_name": "Maria", "score": score},
            headers=auth_headers(),
        )

    response = await client.get("/player/Maria?page=1&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["total"] == 5
    assert len(payload["items"]) == 2


async def test_player_history_missing_player(client):
    response = await client.get("/player/Nobody?page=1&page_size=10")
    assert response.status_code == 404


async def test_player_history_large_pagination(client):
    for value in range(1, 201):
        response = await client.post(
            "/scores",
            json={"player_name": "LoadTestPlayer", "score": value},
            headers=auth_headers(),
        )
        assert response.status_code == 200

    response = await client.get("/player/LoadTestPlayer?page=4&page_size=50")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 200
    assert payload["page"] == 4
    assert payload["page_size"] == 50
    assert len(payload["items"]) == 50
