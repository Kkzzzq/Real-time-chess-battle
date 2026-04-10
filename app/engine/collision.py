from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.domain.models import MatchState, Piece


@dataclass
class CollisionOutcome:
    captured: list[str]
    messages: list[str]


class CollisionResolver:
    @staticmethod
    def resolve_arrivals(state: MatchState, arrived: list[Piece]) -> CollisionOutcome:
        captured: set[str] = set()
        messages: list[str] = []

        by_target: dict[tuple[int, int], list[Piece]] = defaultdict(list)
        for p in arrived:
            if p.alive and p.target is not None:
                by_target[p.target].append(p)

        for target, movers in by_target.items():
            if len(movers) >= 2:
                t = {round(m.move_start_at or 0.0, 4) for m in movers}
                if len(t) == 1:
                    for m in movers:
                        captured.add(m.piece_id)
                    messages.append(f"{target} 同tick对撞同归于尽")
                    continue
                winner = sorted(movers, key=lambda m: m.move_start_at or 0.0)[0]
                for m in movers:
                    if m.piece_id != winner.piece_id:
                        captured.add(m.piece_id)
                messages.append(f"{target} 先启动者 {winner.piece_id} 胜")

        for p in arrived:
            if p.piece_id in captured or not p.alive or p.target is None:
                continue
            for other in state.pieces.values():
                if (
                    other.alive
                    and not other.moving
                    and other.player != p.player
                    and other.x == p.target[0]
                    and other.y == p.target[1]
                ):
                    captured.add(other.piece_id)
                    messages.append(f"{p.piece_id} 吃掉 {other.piece_id}")
                    break

        for pid in captured:
            piece = state.pieces[pid]
            piece.alive = False
            piece.moving = False
            piece.target = None

        return CollisionOutcome(captured=sorted(captured), messages=messages)
