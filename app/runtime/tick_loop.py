from __future__ import annotations

import asyncio
import time
from app.domain.enums import MatchStatus
from app.runtime.broadcaster import Broadcaster
from app.services.match_service import MatchService


class TickLoop:
    def __init__(self, match_service: MatchService, broadcaster: Broadcaster) -> None:
        self.match_service = match_service
        self.broadcaster = broadcaster
        self._tasks: dict[str, asyncio.Task] = {}

    async def ensure_match_loop(self, match_id: str) -> None:
        if match_id in self._tasks and not self._tasks[match_id].done():
            return
        self._tasks[match_id] = asyncio.create_task(self.run_loop(match_id))

    def stop_match_loop(self, match_id: str) -> None:
        task = self._tasks.get(match_id)
        if task and not task.done():
            task.cancel()
        self.broadcaster.cleanup_match(match_id)

    async def run_loop(self, match_id: str) -> None:
        try:
            while True:
                now_ms = int(time.time() * 1000)
                result = self.match_service.tick_once_with_events(match_id, now_ms)
                if result is None:
                    return

                snapshot = result["snapshot"]
                events = result["events"]
                await self.broadcaster.broadcast_snapshot(match_id, snapshot)
                for event in events:
                    await self.broadcaster.broadcast_event(match_id, event)

                status = snapshot["match_meta"]["status"]
                if status == MatchStatus.ENDED.value:
                    await self.broadcaster.broadcast_event(
                        match_id,
                        {"type": "match_ended", "ts_ms": now_ms, "payload": {"match_id": match_id}},
                    )
                    return
                tick_ms = snapshot["match_meta"]["ruleset"].get("tick_ms", 100)
                await asyncio.sleep(tick_ms / 1000)
        finally:
            self._tasks.pop(match_id, None)

    async def shutdown(self) -> None:
        tasks = []
        for m in list(self._tasks.keys()):
            self.stop_match_loop(m)
            t = self._tasks.get(m)
            if t is not None:
                tasks.append(t)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
