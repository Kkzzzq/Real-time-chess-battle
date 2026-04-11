from __future__ import annotations

import pytest
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app


def test_e2e_create_join_ready_start_move_unlock_resign() -> None:
    with TestClient(app) as client:
        match_id = client.post('/matches').json()['match_id']
        p1 = client.post(f'/matches/{match_id}/join', json={'player_name': 'A'}).json()['player']
        p2 = client.post(f'/matches/{match_id}/join', json={'player_name': 'B'}).json()['player']

        client.post(f'/matches/{match_id}/ready', json={'player_id': p1['player_id'], 'player_token': p1['player_token']})
        client.post(f'/matches/{match_id}/ready', json={'player_id': p2['player_id'], 'player_token': p2['player_token']})
        started = client.post(f'/matches/{match_id}/start', json={'player_id': p1['player_id'], 'player_token': p1['player_token']})
        assert started.status_code == 200

        state = client.get(f'/matches/{match_id}/state', params={'player_id': p1['player_id'], 'player_token': p1['player_token']}).json()
        soldier = next(p for p in state['pieces'] if p['owner'] == 1 and p['kind'] == 'soldier')
        legal = client.get(
            f"/matches/{match_id}/pieces/{soldier['id']}/legal-moves",
            params={'player_id': p1['player_id'], 'player_token': p1['player_token']},
        ).json()['actionable']['actionable_targets']
        if legal:
            tx, ty = legal[0]
            mv = client.post(
                f'/matches/{match_id}/commands/move',
                json={'player_id': p1['player_id'], 'player_token': p1['player_token'], 'piece_id': soldier['id'], 'target_x': tx, 'target_y': ty},
            )
            assert mv.status_code == 200

        _ = client.post(f'/matches/{match_id}/commands/unlock', json={'player_id': p1['player_id'], 'player_token': p1['player_token'], 'kind': 'horse'})
        resign = client.post(f'/matches/{match_id}/commands/resign', json={'player_id': p2['player_id'], 'player_token': p2['player_token']})
        assert resign.status_code == 200
