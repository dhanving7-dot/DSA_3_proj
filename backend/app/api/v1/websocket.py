from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/algorithm/{channel}")
async def algorithm_progress_socket(websocket: WebSocket, channel: str):
    """Live algorithm-progress channel. Connect BEFORE triggering a run with a
    matching `channel` (e.g. `playground:<client-id>` for /matching/run, or
    `run:<run_id>` / `run:pending` for /allocation/generate with
    stream_progress=true) to receive GRAPH_CREATED / SEARCHING_AUGMENTING_PATH /
    MATCH_FOUND / MATCH_UPDATED / ALGORITHM_COMPLETE events as they occur.
    """
    await manager.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive / ignored client pings
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
