from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.command_routes import router as command_router
from app.api.match_routes import router as match_router
from app.api.query_routes import router as query_router
from app.api.ws_routes import router as ws_router
from app.container import build_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container()
    try:
        yield
    finally:
        await app.state.container.tick_loop.shutdown()


app = FastAPI(title="Realtime Xiangqi", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match_router)
app.include_router(command_router)
app.include_router(query_router)
app.include_router(ws_router)
