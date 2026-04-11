from __future__ import annotations

from fastapi import Request, WebSocket

from app.container import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_ws_container(websocket: WebSocket) -> AppContainer:
    return websocket.app.state.container
