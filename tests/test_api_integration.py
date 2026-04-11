from __future__ import annotations

import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app


def _boot_match(client: TestClient) -> tuple[str, dict, dict]:
    match = client.post("/matches", json={"ruleset_name": "standard", "allow_draw": True, "tick_ms": 100}).json()
    match_id = match["match_id"]
    p1 = client.post(f"/matches/{match_id}/join", json={"player_name": "A"}).json()["player"]
    p2 = client.post(f"/matches/{match_id}/join", json={"player_name": "B"}).json()["player"]
    required_fields = {"seat", "player_id", "player_token", "player_token_expires_at", "name", "ready", "online", "is_host"}
    assert required_fields.issubset(set(p1.keys()))
    assert required_fields.issubset(set(p2.keys()))
    client.post(f"/matches/{match_id}/ready", json={"player_id": p1["player_id"], "player_token": p1["player_token"]})
    client.post(f"/matches/{match_id}/ready", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
    client.post(f"/matches/{match_id}/start", json={"player_id": p1["player_id"], "player_token": p1["player_token"]})
    return match_id, p1, p2


def test_http_flow_and_state_snapshot() -> None:
    with TestClient(app) as client:
        match_id, p1, _ = _boot_match(client)
        state = client.get(f"/matches/{match_id}/state", params={"player_id": p1["player_id"], "player_token": p1["player_token"]}).json()
        assert state["match_meta"]["status"] == "running"
        assert "runtime_board" in state


def test_start_requires_host() -> None:
    with TestClient(app) as client:
        match_id = client.post("/matches").json()["match_id"]
        p1 = client.post(f"/matches/{match_id}/join", json={"player_name": "A"}).json()["player"]
        p2 = client.post(f"/matches/{match_id}/join", json={"player_name": "B"}).json()["player"]
        client.post(f"/matches/{match_id}/ready", json={"player_id": p1["player_id"], "player_token": p1["player_token"]})
        client.post(f"/matches/{match_id}/ready", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
        not_host = client.post(f"/matches/{match_id}/start", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
        assert not_host.status_code in (400, 403)

def test_query_requires_auth() -> None:
    with TestClient(app) as client:
        match_id, _, _ = _boot_match(client)
        r = client.get(f"/matches/{match_id}/state")
        assert r.status_code in (401, 422)


def test_room_lifecycle_and_offline_reject_command() -> None:
    with TestClient(app) as client:
        match_id = client.post("/matches").json()["match_id"]
        p1 = client.post(f"/matches/{match_id}/join", json={"player_name": "A"}).json()["player"]
        p2 = client.post(f"/matches/{match_id}/join", json={"player_name": "B"}).json()["player"]

        leave_waiting = client.post(
            f"/matches/{match_id}/leave", json={"player_id": p1["player_id"], "player_token": p1["player_token"]}
        ).json()
        assert leave_waiting["players"]["2"]["is_host"] is True

        p1r = client.post(f"/matches/{match_id}/join", json={"player_name": "A2"}).json()["player"]
        client.post(f"/matches/{match_id}/ready", json={"player_id": p1r["player_id"], "player_token": p1r["player_token"]})
        client.post(f"/matches/{match_id}/ready", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
        client.post(f"/matches/{match_id}/start", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})

        client.post(f"/matches/{match_id}/leave", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
        state = client.get(f"/matches/{match_id}/state", params={"player_id": p1r["player_id"], "player_token": p1r["player_token"]}).json()
        soldier = next(p for p in state["pieces"] if p["owner"] == 2 and p["kind"] == "soldier")
        resp = client.post(
            f"/matches/{match_id}/commands/move",
            json={
                "player_id": p2["player_id"],
                "player_token": p2["player_token"],
                "piece_id": soldier["id"],
                "target_x": soldier["x"],
                "target_y": soldier["y"] + 1,
            },
        )
        assert resp.status_code == 403


def test_websocket_requires_auth_and_ping() -> None:
    with TestClient(app) as client:
        match_id, p1, _ = _boot_match(client)
        with client.websocket_connect(f"/matches/{match_id}/ws?player_id={p1['player_id']}&player_token={p1['player_token']}") as ws:
            subscribed = ws.receive_json()
            assert subscribed["type"] == "subscribed"
            ws.receive_json()  # snapshot
            ws.send_json({"type": "ping"})
            pong = ws.receive_json()
            assert pong["type"] == "pong"


def test_reconnect_rejects_expired_token() -> None:
    with TestClient(app) as client:
        match_id = client.post("/matches").json()["match_id"]
        p1 = client.post(f"/matches/{match_id}/join", json={"player_name": "A"}).json()["player"]
        state = client.app.state.container.repo.get_match(match_id)
        for info in state.players.values():
            if info.get("player_id") == p1["player_id"]:
                info["player_token_expires_at"] = 1
        client.app.state.container.repo.save_match(state)
        r = client.post(f"/matches/{match_id}/reconnect", json={"player_id": p1["player_id"], "player_token": p1["player_token"]})
        assert r.status_code == 400
