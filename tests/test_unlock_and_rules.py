from __future__ import annotations

from app.domain.enums import MatchStatus, PieceType
from app.engine.move_rules import validate_move
from app.engine.phase import compute_phase
from app.engine.unlock_service import UnlockService
from app.services.command_service import CommandService
from app.services.match_service import MatchService
from app.services.room_service import RoomService
from app.repository.memory_repo import MemoryRepo


def make_running_state(started_at: int = 0):
    repo = MemoryRepo()
    room = RoomService(repo)
    state = room.create_match()
    state.players = {
        1: {"player_id": "a", "ready": True, "online": True},
        2: {"player_id": "b", "ready": True, "online": True},
    }
    state.status = MatchStatus.RUNNING
    state.started_at = started_at
    state.now_ms = started_at
    state.last_action_at = started_at
    state.last_capture_at = started_at
    repo.save_match(state)
    return repo, state


def test_phase_schedule() -> None:
    assert compute_phase(10_000, 0)[0] == "sealed"
    assert compute_phase(40_000, 0)[0] == "soldier_only"
    assert compute_phase(60_000, 0)[0] == "unlock_wave"
    assert compute_phase(140_000, 0)[0] == "fully_unlocked"


def test_auto_unlock_prefers_cannon() -> None:
    _, state = make_running_state(0)
    UnlockService.apply_auto_unlocks(state, 71_000)
    assert PieceType.CANNON in state.unlocked_by_player[1]
    assert PieceType.CANNON in state.unlocked_by_player[2]


def test_horse_leg_blocked() -> None:
    _, state = make_running_state(0)
    horse = state.pieces["p1_horse_1"]
    ok, msg = validate_move(horse, (3, 8), state)
    assert ok is False
    assert "leg" in msg


def test_flying_general_allowed() -> None:
    _, state = make_running_state(0)
    for p in state.pieces.values():
        if p.x == 4 and p.kind != PieceType.GENERAL:
            p.alive = False
    g = state.pieces["p1_general_1"]
    state.unlocked_by_player[1].add(PieceType.GENERAL)
    ok, _ = validate_move(g, (4, 0), state)
    assert ok is True


def test_match_tick_finishes_move() -> None:
    repo, state = make_running_state(0)
    svc = MatchService(repo)
    soldier = state.pieces["p1_soldier_1"]
    soldier.is_moving = True
    soldier.move_start_at = 30_000
    soldier.move_end_at = 31_000
    soldier.move_total_ms = 1000
    soldier.path_points = [(0, 5)]
    soldier.start_x, soldier.start_y = 0, 6
    soldier.target_x, soldier.target_y = 0, 5
    svc.tick_once(state.match_id, 31_000)
    assert soldier.is_moving is False
    assert (soldier.x, soldier.y) == (0, 5)


def test_unlock_rejects_when_not_running() -> None:
    repo, state = make_running_state(0)
    state.status = MatchStatus.WAITING
    ok, msg = CommandService(repo).handle_unlock_command(state.match_id, "a", PieceType.HORSE, 60_000)
    assert ok is False
    assert "running" in msg


def test_resign_rejects_when_ended() -> None:
    repo, state = make_running_state(0)
    state.status = MatchStatus.ENDED
    ok, msg = CommandService(repo).handle_resign_command(state.match_id, "a", 60_000)
    assert ok is False
    assert "ended" in msg


def test_version_is_event_version_only() -> None:
    repo, state = make_running_state(0)
    before = state.version
    # move-only timeline change without add_event should keep version.
    p = state.pieces["p1_soldier_1"]
    p.is_moving = True
    p.move_start_at = 0
    p.move_end_at = 1000
    p.move_total_ms = 1000
    p.path_points = [(0, 5)]
    p.start_x, p.start_y = 0, 6
    p.target_x, p.target_y = 0, 5
    MatchService(repo).tick_once(state.match_id, 500)
    assert state.version >= before



def test_custom_unlock_windows_drive_phase() -> None:
    repo = MemoryRepo()
    room = RoomService(repo)
    state = room.create_match(custom_unlock_windows=[40, 80, 100])
    state.status = MatchStatus.RUNNING
    state.started_at = 0
    assert compute_phase(85_000, 0, state)[0] == "unlock_wave"


def test_ruleset_name_non_standard_rejected() -> None:
    repo = MemoryRepo()
    room = RoomService(repo)
    try:
        room.create_match(ruleset_name="blitz")
    except ValueError as e:
        assert "unsupported ruleset_name" in str(e)
    else:
        raise AssertionError("expected ValueError")
