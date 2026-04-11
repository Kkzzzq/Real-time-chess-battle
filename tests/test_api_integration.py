from __future__ import annotations

import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app


def _boot_match(client: TestClient) -> tuple[str, str, str]:
    match = client.post("/matches").json()
    match_id = match["match_id"]
    p1 = client.post(f"/matches/{match_id}/join", json={"player_name": "A"}).json()["player"]
    p2 = client.post(f"/matches/{match_id}/join", json={"player_name": "B"}).json()["player"]
    client.post(f"/matches/{match_id}/ready", json={"player_id": p1["player_id"]})
    client.post(f"/matches/{match_id}/ready", json={"player_id": p2["player_id"]})
    client.post(f"/matches/{match_id}/start")
    return match_id, p1["player_id"], p2["player_id"]


def test_http_flow_and_state_snapshot() -> None:
    with TestClient(app) as client:
        match_id, p1_id, _ = _boot_match(client)
        state = client.get(f"/matches/{match_id}/state").json()
        assert state["match_meta"]["status"] == "running"
        assert "runtime_board" in state

        piece_id = next(p["id"] for p in state["pieces"] if p["owner"] == 1 and p["kind"] == "soldier")
        lm = client.get(f"/matches/{match_id}/pieces/{piece_id}/legal-moves", params={"player_id": p1_id}).json()
        assert "static_targets" in lm
        assert "actionable_targets" in lm


def test_websocket_subscribe_ping_and_command() -> None:
    with TestClient(app) as client:
        match_id, p1_id, _ = _boot_match(client)
        with client.websocket_connect(f"/matches/{match_id}/ws") as ws:
            subscribed = ws.receive_json()
            snapshot = ws.receive_json()
            assert subscribed["type"] == "subscribed"
            assert snapshot["type"] == "snapshot"

            ws.send_json({"type": "ping"})
            pong = ws.receive_json()
            assert pong["type"] == "pong"

            soldier = next(p for p in snapshot["data"]["pieces"] if p["owner"] == 1 and p["kind"] == "soldier")
            target_x, target_y = soldier["x"], soldier["y"] - 1
            ws.send_json(
                {
                    "type": "move",
                    "player_id": p1_id,
                    "piece_id": soldier["id"],
                    "target_x": target_x,
                    "target_y": target_y,
                }
            )
            command_result = ws.receive_json()
            events = ws.receive_json()
            snap_after = ws.receive_json()
            assert command_result["type"] == "command_result"
            assert events["type"] == "events"
            assert snap_after["type"] == "snapshot"
