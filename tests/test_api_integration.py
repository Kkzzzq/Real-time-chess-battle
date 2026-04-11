from __future__ import annotations

import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app


def _boot_match(client: TestClient) -> tuple[str, dict, dict]:
    match = client.post("/matches", json={"ruleset_name": "standard", "allow_draw": True, "tick_ms": 100}).json()
    match_id = match["match_id"]
    p1 = client.post(f"/matches/{match_id}/join", json={"player_name": "A"}).json()["player"]
    p2 = client.post(f"/matches/{match_id}/join", json={"player_name": "B"}).json()["player"]
    client.post(f"/matches/{match_id}/ready", json={"player_id": p1["player_id"], "player_token": p1["player_token"]})
    client.post(f"/matches/{match_id}/ready", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
    client.post(f"/matches/{match_id}/start")
    return match_id, p1, p2


def test_http_flow_and_state_snapshot() -> None:
    with TestClient(app) as client:
        match_id, p1, _ = _boot_match(client)
        state = client.get(f"/matches/{match_id}/state", params={"player_id": p1["player_id"], "player_token": p1["player_token"]}).json()
        assert state["match_meta"]["status"] == "running"
        assert "runtime_board" in state
        assert state["match_meta"]["ruleset"]["ruleset_name"] == "standard"
        assert state["players"]["1"]["player_id"] == p1["player_id"]

        piece_id = next(p["id"] for p in state["pieces"] if p["owner"] == 1 and p["kind"] == "soldier")
        lm = client.get(
            f"/matches/{match_id}/pieces/{piece_id}/legal-moves",
            params={"player_id": p1["player_id"], "player_token": p1["player_token"]},
        ).json()
        assert "static" in lm
        assert "actionable" in lm


def test_legal_moves_without_viewer_context() -> None:
    with TestClient(app) as client:
        match_id, _, _ = _boot_match(client)
        state = client.get(f"/matches/{match_id}/state").json()
        piece_id = next(p["id"] for p in state["pieces"] if p["owner"] == 1 and p["kind"] == "soldier")
        lm = client.get(f"/matches/{match_id}/pieces/{piece_id}/legal-moves").json()
        assert lm["actionable"] is None


def test_room_lifecycle_host_transfer_and_offline_reject_command() -> None:
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
        client.post(f"/matches/{match_id}/start")

        client.post(f"/matches/{match_id}/leave", json={"player_id": p2["player_id"], "player_token": p2["player_token"]})
        state = client.get(f"/matches/{match_id}/state").json()
        assert state["players"]["2"]["online"] is False

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


def test_runtime_board_contains_occupants_shape() -> None:
    with TestClient(app) as client:
        match_id, p1, _ = _boot_match(client)
        state = client.get(f"/matches/{match_id}/state", params={"player_id": p1["player_id"], "player_token": p1["player_token"]}).json()
        logical_cell = state["board"]["cells"][9][0]
        runtime_cell = state["runtime_board"]["cells"][9][0]
        assert "occupants" in logical_cell and "primary_occupant" in logical_cell
        assert "occupants" in runtime_cell and "primary_occupant" in runtime_cell


def test_websocket_subscribe_ping_and_command_delta_only() -> None:
    with TestClient(app) as client:
        match_id, p1, _ = _boot_match(client)
        with client.websocket_connect(f"/matches/{match_id}/ws?player_id={p1['player_id']}&player_token={p1['player_token']}") as ws:
            subscribed = ws.receive_json()
            snapshot = ws.receive_json()
            assert subscribed["type"] == "subscribed"
            assert subscribed["data"]["version_semantics"] == "event_version"
            assert snapshot["type"] == "snapshot"

            ws.send_json({"type": "ping"})
            pong = ws.receive_json()
            assert pong["type"] == "pong"

            soldier = next(p for p in snapshot["data"]["pieces"] if p["owner"] == 1 and p["kind"] == "soldier")
            target_x, target_y = soldier["x"], soldier["y"] - 1
            ws.send_json(
                {
                    "type": "move",
                    "player_id": p1["player_id"],
                    "piece_id": soldier["id"],
                    "target_x": target_x,
                    "target_y": target_y,
                }
            )
            command_result = ws.receive_json()
            events = ws.receive_json()
            assert command_result["type"] == "command_result"
            assert events["type"] == "events"
            assert isinstance(events["data"]["events"], list)
