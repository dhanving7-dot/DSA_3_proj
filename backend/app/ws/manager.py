"""Minimal pub/sub WebSocket connection manager, keyed by an arbitrary
channel string (e.g. "playground:<client-generated-id>"). Used to stream
live algorithm-progress events (GRAPH_CREATED, SEARCHING_AUGMENTING_PATH,
MATCH_FOUND, MATCH_UPDATED, ALGORITHM_COMPLETE, ...) to the frontend as an
algorithm executes.
"""
from __future__ import annotations

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(channel, []).append(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        if channel in self.active and websocket in self.active[channel]:
            self.active[channel].remove(websocket)
            if not self.active[channel]:
                del self.active[channel]

    async def broadcast(self, channel: str, message: dict) -> None:
        for websocket in list(self.active.get(channel, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(channel, websocket)


manager = ConnectionManager()


async def replay_steps(
    channel: str,
    steps: list[dict],
    max_total_seconds: float = 4.0,
    min_delay: float = 0.002,
    max_delay: float = 0.03,
) -> None:
    """Re-broadcasts a completed algorithm's real step trace over the given
    channel, pacing it so the UI can animate it live. The per-step delay
    shrinks for large graphs (e.g. a full 220-student dataset can produce
    thousands of steps) so the total replay never drags out past
    `max_total_seconds`, while small graphs still get a readable pace.
    """
    if not steps:
        return
    delay = min(max_delay, max(min_delay, max_total_seconds / len(steps)))
    for step in steps:
        await manager.broadcast(channel, {"type": "ALGORITHM_STEP", **step})
        await asyncio.sleep(delay)
