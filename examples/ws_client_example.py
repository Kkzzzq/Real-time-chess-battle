from __future__ import annotations

import asyncio
import json

import websockets

BASE_WS = "ws://127.0.0.1:8000"
MATCH_ID = "<replace_with_match_id>"
PLAYER_ID = "<replace_with_player_id>"


async def main() -> None:
    async with websockets.connect(f"{BASE_WS}/matches/{MATCH_ID}/ws") as ws:
        print(await ws.recv())  # subscribed
        print(await ws.recv())  # snapshot

        await ws.send(json.dumps({"type": "ping"}))
        print(await ws.recv())

        # move/unlock/resign are command frames
        await ws.send(
            json.dumps(
                {
                    "type": "unlock",
                    "player_id": PLAYER_ID,
                    "kind": "horse",
                }
            )
        )
        print(await ws.recv())  # command_result
        print(await ws.recv())  # events(delta)


if __name__ == "__main__":
    asyncio.run(main())
